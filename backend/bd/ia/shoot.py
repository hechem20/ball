"""
shoot.py
========
Module professionnel de détection et d'analyse des tirs pour un pipeline
d'analyse football (YOLO + tracking + QVAC).

Fonctionnalités :
- Détection d'un événement de tir (accélération brutale du ballon vers
  le but, initiée par un joueur en contrôle)
- Calcul de la puissance du tir (vitesse initiale du ballon)
- Calcul de l'angle de tir par rapport à l'axe du but
- Calcul de la distance au but au moment du tir
- Estimation simplifiée du xG (Expected Goals) à partir de la distance,
  de l'angle et de la puissance
- Détermination du résultat (but, arrêt, hors cadre, contré) à partir
  de la trajectoire du ballon après le tir
- Export JSON des statistiques
- Annotation vidéo (OpenCV)

Dépendances : numpy, opencv-python
"""

from __future__ import annotations

import json
import time
import math
from collections import deque
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Tuple

import numpy as np

try:
    import cv2
except ImportError:
    cv2 = None


# ---------------------------------------------------------------------------
# 1. CONFIGURATION
# ---------------------------------------------------------------------------

@dataclass
class ShootConfig:
    control_distance_px: float = 60.0        # distance sous laquelle un joueur "contrôle" le ballon
    shot_speed_threshold_kmh: float = 40.0    # vitesse mini du ballon pour qualifier un tir
    shot_accel_window_frames: int = 4         # fenêtre d'analyse de l'accélération
    post_shot_track_frames: int = 30          # frames suivies après le tir pour déterminer le résultat
    goal_width_m: float = 7.32
    goal_line_x_m: float = 105.0              # position de la ligne de but (longueur du terrain)
    field_width_m: float = 68.0
    goal_center_y_m: float = 34.0             # centre du but (milieu de la largeur du terrain)
    outside_frame_margin_m: float = 1.0       # marge pour considérer un tir "hors cadre"


class ShotResult(str, Enum):
    GOAL = "but"
    SAVED = "arrete"
    OFF_TARGET = "hors_cadre"
    BLOCKED = "contre"
    UNKNOWN = "indetermine"


# ---------------------------------------------------------------------------
# 2. STRUCTURES DE DONNÉES
# ---------------------------------------------------------------------------

@dataclass
class ShotEvent:
    shooter_id: int
    frame_index: int
    shot_pos_m: Tuple[float, float]
    initial_speed_kmh: float
    angle_deg: float
    distance_to_goal_m: float
    xg: float
    result: ShotResult = ShotResult.UNKNOWN

    def to_dict(self) -> dict:
        return {
            "shooter_id": self.shooter_id,
            "frame_index": self.frame_index,
            "shot_position_m": [round(c, 1) for c in self.shot_pos_m],
            "initial_speed_kmh": round(self.initial_speed_kmh, 1),
            "angle_deg": round(self.angle_deg, 1),
            "distance_to_goal_m": round(self.distance_to_goal_m, 1),
            "xg": round(self.xg, 3),
            "result": self.result.value,
        }


# ---------------------------------------------------------------------------
# 3. ANALYSEUR DE TIRS
# ---------------------------------------------------------------------------

class ShootAnalyzer:
    """
    Détecte les tirs à partir d'un flux de positions du ballon (en mètres,
    déjà calibrées) et du contrôleur courant (typiquement fourni par
    control.py). Un tir est identifié par une forte accélération du ballon
    au moment où un joueur le quitte, orientée vers le but adverse.
    """

    def __init__(self, config: Optional[ShootConfig] = None, fps: float = 30.0):
        self.config = config or ShootConfig()
        self.fps = fps
        self.dt = 1.0 / fps

        self._ball_history: deque = deque(maxlen=self.config.shot_accel_window_frames + 2)
        self._last_controller_id: Optional[int] = None

        self._pending_shot: Optional[ShotEvent] = None
        self._pending_track: List[Tuple[float, float]] = []

        self.events: List[ShotEvent] = []
        self.player_stats: Dict[int, dict] = {}

        self.frame_index = 0

    # ---- API principale -----------------------------------------------------

    def update_frame(self, ball_pos_m: Optional[Tuple[float, float]],
                      controller_id: Optional[int]) -> Optional[ShotEvent]:
        """
        À appeler à chaque frame. Retourne un ShotEvent finalisé (résultat
        déterminé) lorsque le suivi post-tir est terminé, sinon None.
        """
        self.frame_index += 1
        finalized: Optional[ShotEvent] = None

        if ball_pos_m is not None:
            self._ball_history.append((self.frame_index, ball_pos_m))

        # Poursuite du suivi d'un tir en cours pour déterminer son résultat
        if self._pending_shot is not None:
            if ball_pos_m is not None:
                self._pending_track.append(ball_pos_m)

            frames_since_shot = self.frame_index - self._pending_shot.frame_index
            if frames_since_shot >= self.config.post_shot_track_frames or ball_pos_m is None:
                self._pending_shot.result = self._determine_result(self._pending_track)
                self.events.append(self._pending_shot)
                self._record_stats(self._pending_shot)
                finalized = self._pending_shot
                self._pending_shot = None
                self._pending_track = []

        # Détection d'un nouveau tir : le joueur qui contrôlait le ballon
        # vient de le relâcher avec une forte accélération vers le but
        elif (self._last_controller_id is not None and
              controller_id != self._last_controller_id and
              len(self._ball_history) >= self.config.shot_accel_window_frames):

            shot = self._try_detect_shot(self._last_controller_id)
            if shot is not None:
                self._pending_shot = shot
                self._pending_track = [shot.shot_pos_m]

        if controller_id is not None:
            self._last_controller_id = controller_id

        return finalized

    # ---- Logique interne ------------------------------------------------------

    def _try_detect_shot(self, shooter_id: int) -> Optional[ShotEvent]:
        cfg = self.config
        recent = list(self._ball_history)[-cfg.shot_accel_window_frames:]
        if len(recent) < 2:
            return None

        (f_start, p_start), (f_end, p_end) = recent[0], recent[-1]
        dt = max(1, f_end - f_start) * self.dt
        distance_m = math.hypot(p_end[0] - p_start[0], p_end[1] - p_start[1])
        speed_kmh = (distance_m / dt) * 3.6

        if speed_kmh < cfg.shot_speed_threshold_kmh:
            return None

        # Le tir doit être orienté vers le but adverse (x croissant)
        if p_end[0] <= p_start[0]:
            return None

        angle_deg = self._shot_angle(p_start)
        distance_to_goal = self._distance_to_goal(p_start)
        xg = self._estimate_xg(distance_to_goal, angle_deg, speed_kmh)

        return ShotEvent(
            shooter_id=shooter_id,
            frame_index=f_end,
            shot_pos_m=p_start,
            initial_speed_kmh=speed_kmh,
            angle_deg=angle_deg,
            distance_to_goal_m=distance_to_goal,
            xg=xg,
        )

    def _distance_to_goal(self, pos_m: Tuple[float, float]) -> float:
        cfg = self.config
        return math.hypot(cfg.goal_line_x_m - pos_m[0], cfg.goal_center_y_m - pos_m[1])

    def _shot_angle(self, pos_m: Tuple[float, float]) -> float:
        """
        Angle (en degrés) entre la position de tir et les deux poteaux du but.
        Un angle plus grand = meilleure position de tir (plus de cage visible).
        """
        cfg = self.config
        post1 = (cfg.goal_line_x_m, cfg.goal_center_y_m - cfg.goal_width_m / 2)
        post2 = (cfg.goal_line_x_m, cfg.goal_center_y_m + cfg.goal_width_m / 2)

        v1 = (post1[0] - pos_m[0], post1[1] - pos_m[1])
        v2 = (post2[0] - pos_m[0], post2[1] - pos_m[1])

        norm1 = math.hypot(*v1)
        norm2 = math.hypot(*v2)
        if norm1 == 0 or norm2 == 0:
            return 0.0

        cos_angle = (v1[0] * v2[0] + v1[1] * v2[1]) / (norm1 * norm2)
        cos_angle = max(-1.0, min(1.0, cos_angle))
        return math.degrees(math.acos(cos_angle))

    @staticmethod
    def _estimate_xg(distance_m: float, angle_deg: float, speed_kmh: float) -> float:
        """
        Modèle xG simplifié (approximation logistique), calibré grossièrement :
        - la probabilité diminue avec la distance
        - augmente avec l'angle de tir disponible
        - augmente légèrement avec la puissance du tir (jusqu'à un plafond)
        Ce n'est PAS un modèle statistique entraîné sur données réelles,
        mais une heuristique raisonnable pour une démo.
        """
        distance_term = -0.10 * distance_m
        angle_term = 0.045 * angle_deg
        power_term = 0.01 * min(speed_kmh, 100.0)

        z = -1.0 + distance_term + angle_term + power_term
        xg = 1.0 / (1.0 + math.exp(-z))
        return max(0.01, min(0.95, xg))

    def _determine_result(self, track_m: List[Tuple[float, float]]) -> ShotResult:
        """
        Détermine le résultat du tir à partir de la trajectoire suivie
        après l'impact. Heuristique basée sur la position finale du ballon
        par rapport au cadre du but.
        """
        cfg = self.config
        if not track_m:
            return ShotResult.UNKNOWN

        final_pos = track_m[-1]
        reached_goal_line = final_pos[0] >= cfg.goal_line_x_m - 1.0

        if not reached_goal_line:
            # Le ballon n'a jamais atteint la ligne de but : contré ou raté
            max_x = max(p[0] for p in track_m)
            if max_x < cfg.goal_line_x_m - 5.0:
                return ShotResult.BLOCKED
            return ShotResult.OFF_TARGET

        y_at_goal = final_pos[1]
        goal_bottom = cfg.goal_center_y_m - cfg.goal_width_m / 2
        goal_top = cfg.goal_center_y_m + cfg.goal_width_m / 2

        within_frame = goal_bottom <= y_at_goal <= goal_top

        if not within_frame:
            return ShotResult.OFF_TARGET

        # Simplification : si le ballon atteint le cadre et continue
        # d'avancer jusqu'à la ligne sans être dévié, on considère un but.
        # Un vrai système croiserait ceci avec la détection du gardien.
        return ShotResult.GOAL

    def _record_stats(self, event: ShotEvent) -> None:
        stats = self.player_stats.setdefault(event.shooter_id, {
            "shots": 0,
            "goals": 0,
            "on_target": 0,
            "total_xg": 0.0,
        })
        stats["shots"] += 1
        stats["total_xg"] += event.xg

        if event.result == ShotResult.GOAL:
            stats["goals"] += 1
            stats["on_target"] += 1
        elif event.result == ShotResult.SAVED:
            stats["on_target"] += 1

    # ---- Statistiques agrégées -------------------------------------------------

    def get_player_summary(self, player_id: int) -> dict:
        stats = self.player_stats.get(player_id)
        if stats is None:
            return {"player_id": player_id, "shots": 0}

        shots = stats["shots"]
        accuracy_percent = round(100 * stats["on_target"] / shots, 1) if shots else 0.0

        return {
            "player_id": player_id,
            "shots": shots,
            "goals": stats["goals"],
            "on_target": stats["on_target"],
            "accuracy_percent": accuracy_percent,
            "total_xg": round(stats["total_xg"], 2),
        }

    def get_summary(self) -> List[dict]:
        return [self.get_player_summary(pid) for pid in self.player_stats]

    def export_json(self, path: str) -> None:
        data = {
            "generated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            "fps": self.fps,
            "total_shots": len(self.events),
            "shots": [e.to_dict() for e in self.events],
            "players": self.get_summary(),
        }
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    # ---- Annotation vidéo ---------------------------------------------------

    def annotate_frame(self, frame, last_event: Optional[ShotEvent]):
        if cv2 is None:
            raise ImportError("OpenCV est requis pour l'annotation vidéo.")
        if last_event is None:
            return frame

        result_colors = {
            ShotResult.GOAL: (0, 255, 0),
            ShotResult.SAVED: (0, 255, 255),
            ShotResult.OFF_TARGET: (0, 0, 255),
            ShotResult.BLOCKED: (255, 0, 0),
            ShotResult.UNKNOWN: (200, 200, 200),
        }
        color = result_colors.get(last_event.result, (255, 255, 255))

        label = f"Tir joueur {last_event.shooter_id} | {last_event.result.value.upper()}"
        cv2.putText(frame, label, (30, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.75, color, 2)

        details = (f"{last_event.initial_speed_kmh:.1f} km/h | "
                   f"angle {last_event.angle_deg:.1f} deg | xG {last_event.xg:.2f}")
        cv2.putText(frame, details, (30, 70), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

        return frame


# ---------------------------------------------------------------------------
# 4. EXEMPLE D'UTILISATION
# ---------------------------------------------------------------------------

