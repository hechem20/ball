"""

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
class PassConfig:
    control_distance_px: float = 60.0        # distance sous laquelle un joueur "contrôle" le ballon
    min_pass_distance_px: float = 40.0        # distance minimale pour valider un événement de passe
    max_pass_gap_frames: int = 90             # durée max (frames) entre perte et réception
    short_pass_max_m: float = 15.0            # seuil passe courte
    long_pass_min_m: float = 30.0             # seuil passe longue
    through_ball_min_speed_kmh: float = 45.0  # vitesse mini pour considérer "passe en profondeur"
    cross_zone_x_ratio: float = 0.2           # zone latérale (proche des lignes de touche) pour un centre
    field_width_m: float = 68.0
    field_length_m: float = 105.0


class PassType(str, Enum):
    SHORT = "courte"
    LONG = "longue"
    THROUGH_BALL = "en profondeur"
    CROSS = "centre"
    BACK_PASS = "en retrait"


# ---------------------------------------------------------------------------
# 2. STRUCTURES DE DONNÉES
# ---------------------------------------------------------------------------

@dataclass
class PassEvent:
    sender_id: int
    receiver_id: Optional[int]
    start_frame: int
    end_frame: int
    start_pos_m: Tuple[float, float]
    end_pos_m: Tuple[float, float]
    ball_speed_kmh: float
    distance_m: float
    pass_type: PassType
    successful: bool
    accuracy_score: float

    def to_dict(self) -> dict:
        return {
            "sender_id": self.sender_id,
            "receiver_id": self.receiver_id,
            "start_frame": self.start_frame,
            "end_frame": self.end_frame,
            "distance_m": round(self.distance_m, 1),
            "ball_speed_kmh": round(self.ball_speed_kmh, 1),
            "pass_type": self.pass_type.value,
            "successful": self.successful,
            "accuracy_score": round(self.accuracy_score, 1),
        }


# ---------------------------------------------------------------------------
# 3. ANALYSEUR DE PASSES
# ---------------------------------------------------------------------------

class PassAnalyzer:
    """
    Détecte les événements de passe à partir d'un flux de :
    - position du ballon par frame (en mètres, déjà calibrée)
    - contrôleur du ballon par frame (player_id ou None), typiquement
      fourni par control.py (BallControlAnalyzer)

    Utilisation typique : appeler update_frame() à chaque frame avec
    l'état courant du contrôle, en parallèle du BallControlAnalyzer.
    """

    def __init__(self, config: Optional[PassConfig] = None, fps: float = 30.0):
        self.config = config or PassConfig()
        self.fps = fps
        self.dt = 1.0 / fps

        self._last_controller_id: Optional[int] = None
        self._last_controller_frame: int = 0
        self._last_controller_pos_m: Optional[Tuple[float, float]] = None

        self._ball_positions: deque = deque(maxlen=self.config.max_pass_gap_frames + 5)
        self._pending_release: Optional[dict] = None

        self.events: List[PassEvent] = []
        self.player_stats: Dict[int, dict] = {}

        self.frame_index = 0

    # ---- API principale -----------------------------------------------------

    def update_frame(self, ball_pos_m: Optional[Tuple[float, float]],
                      controller_id: Optional[int]) -> Optional[PassEvent]:
        """
        À appeler à chaque frame.
        Retourne un PassEvent si une passe vient d'être finalisée sur cette
        frame, sinon None.
        """
        self.frame_index += 1
        result: Optional[PassEvent] = None

        if ball_pos_m is not None:
            self._ball_positions.append((self.frame_index, ball_pos_m))

        # Cas 1 : le ballon vient de quitter un joueur -> potentiel départ de passe
        if (self._last_controller_id is not None and
                controller_id != self._last_controller_id and
                self._pending_release is None):

            self._pending_release = {
                "sender_id": self._last_controller_id,
                "start_frame": self._last_controller_frame,
                "start_pos_m": self._last_controller_pos_m,
            }

        # Cas 2 : un joueur reprend le contrôle -> finalise (ou invalide) la passe en attente
        if controller_id is not None and self._pending_release is not None:
            pending = self._pending_release
            gap = self.frame_index - pending["start_frame"]

            if gap <= self.config.max_pass_gap_frames and ball_pos_m is not None:
                event = self._finalize_pass(
                    pending, receiver_id=controller_id,
                    end_frame=self.frame_index, end_pos_m=ball_pos_m,
                )
                if event is not None:
                    self.events.append(event)
                    self._record_stats(event)
                    result = event

            self._pending_release = None

        # Passe ratée : le délai maximum est dépassé sans reprise de contrôle
        elif (self._pending_release is not None and
              self.frame_index - self._pending_release["start_frame"] > self.config.max_pass_gap_frames):
            pending = self._pending_release
            last_known_pos = self._ball_positions[-1][1] if self._ball_positions else pending["start_pos_m"]
            event = self._finalize_pass(
                pending, receiver_id=None,
                end_frame=self.frame_index, end_pos_m=last_known_pos,
            )
            if event is not None:
                self.events.append(event)
                self._record_stats(event)
                result = event
            self._pending_release = None

        if controller_id is not None and ball_pos_m is not None:
            self._last_controller_id = controller_id
            self._last_controller_frame = self.frame_index
            self._last_controller_pos_m = ball_pos_m

        return result

    # ---- Logique interne ------------------------------------------------------

    def _finalize_pass(self, pending: dict, receiver_id: Optional[int],
                        end_frame: int, end_pos_m: Tuple[float, float]) -> Optional[PassEvent]:
        start_pos = pending["start_pos_m"]
        if start_pos is None:
            return None

        distance_m = math.hypot(end_pos_m[0] - start_pos[0], end_pos_m[1] - start_pos[1])

        if distance_m < self.config.min_pass_distance_px / 100.0 * 10:
            # distance trop faible pour être considérée comme une vraie passe
            # (évite de compter les micro-mouvements comme des passes)
            pass

        duration_frames = max(1, end_frame - pending["start_frame"])
        duration_s = duration_frames * self.dt
        speed_m_s = distance_m / duration_s if duration_s > 0 else 0.0
        speed_kmh = speed_m_s * 3.6

        pass_type = self._classify_pass(start_pos, end_pos_m, speed_kmh)

        successful = receiver_id is not None and receiver_id != pending["sender_id"]
        accuracy_score = self._accuracy_score(successful, distance_m, speed_kmh)

        return PassEvent(
            sender_id=pending["sender_id"],
            receiver_id=receiver_id,
            start_frame=pending["start_frame"],
            end_frame=end_frame,
            start_pos_m=start_pos,
            end_pos_m=end_pos_m,
            ball_speed_kmh=speed_kmh,
            distance_m=distance_m,
            pass_type=pass_type,
            successful=successful,
            accuracy_score=accuracy_score,
        )

    def _classify_pass(self, start_pos: Tuple[float, float],
                        end_pos: Tuple[float, float],
                        speed_kmh: float) -> PassType:
        cfg = self.config
        dx = end_pos[0] - start_pos[0]
        dy = end_pos[1] - start_pos[1]
        distance_m = math.hypot(dx, dy)

        # Passe en retrait : le ballon revient vers son propre camp (x diminue nettement)
        if dx < -5.0:
            return PassType.BACK_PASS

        # Centre : le ballon part d'une zone latérale (proche des lignes de touche)
        # vers le centre du terrain
        lateral_zone = cfg.field_width_m * cfg.cross_zone_x_ratio
        if start_pos[1] <= lateral_zone or start_pos[1] >= (cfg.field_width_m - lateral_zone):
            if abs(dy) > 10.0:
                return PassType.CROSS

        # Passe en profondeur : vitesse élevée + progression verticale marquée
        if speed_kmh >= cfg.through_ball_min_speed_kmh and dx > 15.0:
            return PassType.THROUGH_BALL

        if distance_m >= cfg.long_pass_min_m:
            return PassType.LONG

        return PassType.SHORT

    @staticmethod
    def _accuracy_score(successful: bool, distance_m: float, speed_kmh: float) -> float:
        if not successful:
            return 0.0

        # Score de base pour une passe réussie
        score = 80.0

        # Bonus pour les passes longues réussies (plus difficiles)
        if distance_m >= 30.0:
            score += 10.0
        elif distance_m >= 15.0:
            score += 5.0

        # Malus léger si la vitesse est excessive (risque de perte de contrôle du récepteur)
        if speed_kmh > 90.0:
            score -= 5.0

        return max(0.0, min(100.0, score))

    def _record_stats(self, event: PassEvent) -> None:
        sender_stats = self.player_stats.setdefault(event.sender_id, {
            "passes_attempted": 0,
            "passes_completed": 0,
            "total_distance_m": 0.0,
            "pass_types": {},
        })
        sender_stats["passes_attempted"] += 1
        sender_stats["total_distance_m"] += event.distance_m
        if event.successful:
            sender_stats["passes_completed"] += 1

        type_counts = sender_stats["pass_types"]
        type_counts[event.pass_type.value] = type_counts.get(event.pass_type.value, 0) + 1

    # ---- Statistiques agrégées -------------------------------------------------

    def get_player_summary(self, player_id: int) -> dict:
        stats = self.player_stats.get(player_id)
        if stats is None:
            return {"player_id": player_id, "passes_attempted": 0}

        attempted = stats["passes_attempted"]
        completed = stats["passes_completed"]
        accuracy_percent = round(100 * completed / attempted, 1) if attempted else 0.0

        return {
            "player_id": player_id,
            "passes_attempted": attempted,
            "passes_completed": completed,
            "accuracy_percent": accuracy_percent,
            "total_distance_m": round(stats["total_distance_m"], 1),
            "pass_types": stats["pass_types"],
        }

    def get_summary(self) -> List[dict]:
        return [self.get_player_summary(pid) for pid in self.player_stats]

    def export_json(self, path: str) -> None:
        data = {
            "generated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            "fps": self.fps,
            "total_events": len(self.events),
            "events": [e.to_dict() for e in self.events],
            "players": self.get_summary(),
        }
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    # ---- Annotation vidéo ---------------------------------------------------

    def annotate_frame(self, frame, last_event: Optional[PassEvent]):
        if cv2 is None:
            raise ImportError("OpenCV est requis pour l'annotation vidéo.")
        if last_event is None:
            return frame

        status = "REUSSIE" if last_event.successful else "RATEE"
        color = (0, 255, 0) if last_event.successful else (0, 0, 255)

        label = (f"Passe {last_event.pass_type.value} | {last_event.sender_id} -> "
                 f"{last_event.receiver_id or '?'} | {status}")

        cv2.putText(frame, label, (30, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
        cv2.putText(
            frame, f"{last_event.ball_speed_kmh:.1f} km/h | {last_event.distance_m:.1f} m",
            (30, 70), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2,
        )

        return frame

 