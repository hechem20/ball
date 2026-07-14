"""
control.py
==========
Module professionnel d'analyse du contrôle de balle pour un pipeline
d'analyse football (YOLO + tracking + QVAC).

Fonctionnalités :
- Suivi de la position du ballon (lissé par Kalman)
- Détection des contacts pied-ballon (touches)
- Calcul du temps de possession par joueur
- Score de contrôle global (distance, stabilité, touches, dribbles)
- Détection de séquences de dribble (changements de direction sous contrôle)
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
from typing import Dict, List, Optional, Tuple

import numpy as np

try:
    import cv2
except ImportError:
    cv2 = None

# Réutilise le filtre de Kalman défini dans speed.py pour rester cohérent
try:
    from speed import KalmanPositionFilter
except ImportError:
    # Fallback minimal si speed.py n'est pas dans le même dossier
    class KalmanPositionFilter:
        def __init__(self, dt: float = 1 / 30, process_noise: float = 1.0,
                     measurement_noise: float = 5.0):
            self.dt = dt
            self.x = np.zeros((4, 1))
            self.F = np.array([[1, 0, dt, 0], [0, 1, 0, dt],
                                [0, 0, 1, 0], [0, 0, 0, 1]], dtype=np.float64)
            self.H = np.array([[1, 0, 0, 0], [0, 1, 0, 0]], dtype=np.float64)
            self.Q = np.eye(4) * process_noise
            self.R = np.eye(2) * measurement_noise
            self.P = np.eye(4) * 500.0
            self.initialized = False

        def init(self, x, y):
            self.x = np.array([[x], [y], [0.0], [0.0]])
            self.P = np.eye(4) * 500.0
            self.initialized = True

        def update(self, x, y):
            if not self.initialized:
                self.init(x, y)
                return tuple(self.x.flatten())
            z = np.array([[x], [y]])
            y_err = z - (self.H @ self.x)
            S = self.H @ self.P @ self.H.T + self.R
            K = self.P @ self.H.T @ np.linalg.inv(S)
            self.x = self.x + K @ y_err
            self.P = (np.eye(4) - K @ self.H) @ self.P
            return tuple(self.x.flatten())

        @property
        def position(self):
            return float(self.x[0, 0]), float(self.x[1, 0])


# ---------------------------------------------------------------------------
# 1. PARAMÈTRES DE DÉTECTION
# ---------------------------------------------------------------------------

@dataclass
class ControlConfig:
    contact_distance_px: float = 45.0       # distance pied-ballon considérée comme contact
    control_distance_px: float = 60.0       # distance max pour rester "sous contrôle"
    min_frames_for_touch: int = 2           # frames consécutives minimum pour valider une touche
    dribble_angle_threshold_deg: float = 35.0  # changement de direction minimum pour un dribble
    dribble_window_frames: int = 10         # fenêtre d'analyse pour détecter un dribble
    stability_speed_threshold: float = 8.0  # variation de vitesse (m/s) tolérée pour "stable"


# ---------------------------------------------------------------------------
# 2. SUIVI DU BALLON
# ---------------------------------------------------------------------------

@dataclass
class BallTouch:
    frame_index: int
    player_id: int
    x_px: float
    y_px: float
    foot: str  # "left" ou "right"


class BallTracker:
    """Suivi lissé de la position du ballon, image par image."""

    def __init__(self, dt: float = 1 / 30):
        self.kalman = KalmanPositionFilter(dt=dt)
        self.history_px: deque = deque(maxlen=300)
        self.speed_history: deque = deque(maxlen=10)
        self._last_pos: Optional[Tuple[float, float]] = None
        self.dt = dt

    def update(self, x_px: float, y_px: float) -> Tuple[float, float]:
        fx, fy, vx, vy = self.kalman.update(x_px, y_px)
        self.history_px.append((fx, fy))

        speed_px_s = math.hypot(vx, vy)
        self.speed_history.append(speed_px_s)

        self._last_pos = (fx, fy)
        return fx, fy

    @property
    def position(self) -> Optional[Tuple[float, float]]:
        return self._last_pos

    @property
    def speed_variability(self) -> float:
        """Écart-type de la vitesse récente du ballon (mesure de stabilité)."""
        if len(self.speed_history) < 2:
            return 0.0
        return float(np.std(self.speed_history))


# ---------------------------------------------------------------------------
# 3. ANALYSE DE CONTRÔLE PAR JOUEUR
# ---------------------------------------------------------------------------

@dataclass
class PlayerControlStats:
    player_id: int
    frames_in_control: int = 0
    total_frames_tracked: int = 0
    touches: List[BallTouch] = field(default_factory=list)
    dribble_count: int = 0
    control_states: deque = field(default_factory=lambda: deque(maxlen=600))

    @property
    def possession_percent(self) -> float:
        if self.total_frames_tracked == 0:
            return 0.0
        return round(100 * self.frames_in_control / self.total_frames_tracked, 1)

    @property
    def touch_count(self) -> int:
        return len(self.touches)


class BallControlAnalyzer:
    """
    Point d'entrée principal du module.
    Combine la position du ballon et les positions des pieds de chaque
    joueur pour calculer possession, touches, stabilité et dribbles.
    """

    def __init__(self, config: Optional[ControlConfig] = None, fps: float = 30.0):
        self.config = config or ControlConfig()
        self.fps = fps
        self.dt = 1.0 / fps
        self.ball = BallTracker(dt=self.dt)
        self.players: Dict[int, PlayerControlStats] = {}
        self.frame_index = 0
        self._last_controller_id: Optional[int] = None
        self._direction_buffer: Dict[int, deque] = {}

    def _get_player(self, player_id: int) -> PlayerControlStats:
        if player_id not in self.players:
            self.players[player_id] = PlayerControlStats(player_id=player_id)
            self._direction_buffer[player_id] = deque(maxlen=self.config.dribble_window_frames)
        return self.players[player_id]

    @staticmethod
    def _distance(p1: Tuple[float, float], p2: Tuple[float, float]) -> float:
        return math.hypot(p1[0] - p2[0], p1[1] - p2[1])

    def update_frame(self,
                      ball_bbox: Optional[Tuple[float, float, float, float]],
                      players_feet: Dict[int, Dict[str, Tuple[float, float]]]
                      ) -> Optional[dict]:
        """
        ball_bbox : (x1, y1, x2, y2) du ballon détecté (YOLO), ou None si non détecté.
        players_feet : {player_id: {"left": (x,y), "right": (x,y)}}

        Retourne un dict décrivant l'état de la frame courante (ou None si pas de ballon).
        """
        self.frame_index += 1

        if ball_bbox is None:
            return None

        bx = (ball_bbox[0] + ball_bbox[2]) / 2
        by = (ball_bbox[1] + ball_bbox[3]) / 2
        ball_pos = self.ball.update(bx, by)

        nearest_player_id = None
        nearest_distance = float("inf")
        nearest_foot = None

        for player_id, feet in players_feet.items():
            stats = self._get_player(player_id)
            stats.total_frames_tracked += 1

            d_left = self._distance(ball_pos, feet["left"])
            d_right = self._distance(ball_pos, feet["right"])

            if d_left <= d_right:
                dist, foot = d_left, "left"
            else:
                dist, foot = d_right, "right"

            if dist < nearest_distance:
                nearest_distance = dist
                nearest_player_id = player_id
                nearest_foot = foot

        frame_result = {
            "frame_index": self.frame_index,
            "ball_position": ball_pos,
            "controller_id": None,
            "state": "LOOSE_BALL",
            "distance_px": None,
        }

        if nearest_player_id is None:
            return frame_result

        stats = self._get_player(nearest_player_id)

        if nearest_distance <= self.config.control_distance_px:
            stats.frames_in_control += 1
            state = "CONTROL"
            frame_result["controller_id"] = nearest_player_id
            frame_result["state"] = state

            # Détection de touche : contact rapproché + changement de contrôleur
            if nearest_distance <= self.config.contact_distance_px:
                if self._last_controller_id != nearest_player_id:
                    touch = BallTouch(
                        frame_index=self.frame_index,
                        player_id=nearest_player_id,
                        x_px=ball_pos[0],
                        y_px=ball_pos[1],
                        foot=nearest_foot,
                    )
                    stats.touches.append(touch)

            self._update_dribble_detection(nearest_player_id, ball_pos)
            self._last_controller_id = nearest_player_id
        else:
            frame_result["state"] = "LOST"
            self._last_controller_id = None

        frame_result["distance_px"] = round(nearest_distance, 1)
        stats.control_states.append(frame_result["state"])

        return frame_result

    def _update_dribble_detection(self, player_id: int, ball_pos: Tuple[float, float]) -> None:
        """
        Détecte un dribble comme un changement de direction significatif
        du ballon pendant que le joueur en garde le contrôle.
        """
        buf = self._direction_buffer[player_id]
        buf.append(ball_pos)

        if len(buf) < self.config.dribble_window_frames:
            return

        p_start, p_mid, p_end = buf[0], buf[len(buf) // 2], buf[-1]

        v1 = (p_mid[0] - p_start[0], p_mid[1] - p_start[1])
        v2 = (p_end[0] - p_mid[0], p_end[1] - p_mid[1])

        angle = self._angle_between(v1, v2)

        if angle >= self.config.dribble_angle_threshold_deg:
            self.players[player_id].dribble_count += 1
            buf.clear()

    @staticmethod
    def _angle_between(v1: Tuple[float, float], v2: Tuple[float, float]) -> float:
        norm1 = math.hypot(*v1)
        norm2 = math.hypot(*v2)
        if norm1 == 0 or norm2 == 0:
            return 0.0
        cos_angle = (v1[0] * v2[0] + v1[1] * v2[1]) / (norm1 * norm2)
        cos_angle = max(-1.0, min(1.0, cos_angle))
        return math.degrees(math.acos(cos_angle))

    # ---- Score global -----------------------------------------------------

    def control_score(self, player_id: int) -> dict:
        """
        Calcule un score global de contrôle sur 100, combinant :
        - distance moyenne pied-ballon pendant le contrôle
        - possession (%)
        - qualité des touches
        - stabilité de la vitesse du ballon
        - compétence de dribble
        """
        stats = self.players.get(player_id)
        if stats is None or stats.total_frames_tracked == 0:
            return {"player_id": player_id, "overall": 0.0}

        possession_score = min(100.0, stats.possession_percent)

        touch_quality = min(100.0, stats.touch_count * 6.0)

        variability = self.ball.speed_variability
        stability_score = max(0.0, 100.0 - variability * 5.0)

        dribble_score = min(100.0, stats.dribble_count * 12.0)

        # La distance moyenne pied-ballon est approximée à partir du seuil de contrôle
        distance_score = 90.0 if stats.possession_percent > 50 else 70.0

        overall = round(
            distance_score * 0.25 +
            possession_score * 0.30 +
            touch_quality * 0.20 +
            stability_score * 0.15 +
            dribble_score * 0.10,
            1,
        )

        return {
            "player_id": player_id,
            "distance_score": round(distance_score, 1),
            "possession_score": round(possession_score, 1),
            "touch_quality": round(touch_quality, 1),
            "stability_score": round(stability_score, 1),
            "dribble_score": round(dribble_score, 1),
            "overall": overall,
        }

    def get_summary(self) -> List[dict]:
        summaries = []
        for player_id, stats in self.players.items():
            summary = {
                "player_id": player_id,
                "possession_percent": stats.possession_percent,
                "touch_count": stats.touch_count,
                "dribble_count": stats.dribble_count,
            }
            summary.update({"score": self.control_score(player_id)["overall"]})
            summaries.append(summary)
        return summaries

    def export_json(self, path: str) -> None:
        data = {
            "generated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            "fps": self.fps,
            "players": self.get_summary(),
        }
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    # ---- Annotation vidéo ---------------------------------------------------

    def annotate_frame(self, frame, frame_result: Optional[dict]):
        if cv2 is None:
            raise ImportError("OpenCV est requis pour l'annotation vidéo.")
        if frame_result is None:
            return frame

        state = frame_result["state"]
        color = (0, 255, 0) if state == "CONTROL" else (0, 0, 255)

        cv2.putText(
            frame, f"State: {state}", (30, 40),
            cv2.FONT_HERSHEY_SIMPLEX, 1, color, 2,
        )

        controller = frame_result.get("controller_id")
        if controller is not None:
            score = self.control_score(controller)["overall"]
            cv2.putText(
                frame, f"Player {controller} | Control Score: {score}%",
                (30, 80), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2,
            )

        return frame


