"""
pose.py
=======
Extraction de la position des pieds de chaque joueur détecté, via
MediaPipe Pose appliqué sur la région recadrée (bbox) de chaque joueur.

Dépendances : mediapipe, opencv-python, numpy
"""

from __future__ import annotations

from typing import Dict, Optional, Tuple

import numpy as np

try:
    import mediapipe as mp
except ImportError:
    mp = None

from ia.detector import Detection


class FeetExtractor:
    """
    Pour chaque joueur détecté (bbox), recadre l'image et lance MediaPipe
    Pose dessus pour localiser les pieds, puis reprojette les coordonnées
    dans le référentiel de l'image complète.
    """

    LEFT_FOOT_INDEX = 31
    RIGHT_FOOT_INDEX = 32

    def __init__(self, model_complexity: int = 1, min_detection_confidence: float = 0.5):
        if mp is None:
            raise ImportError(
                "Le package 'mediapipe' est requis. Installe-le avec : "
                "pip install mediapipe"
            )

        self._pose = mp.solutions.pose.Pose(
            static_image_mode=False,
            model_complexity=model_complexity,
            min_detection_confidence=min_detection_confidence,
        )

    def extract_feet(self, frame: np.ndarray, player_bbox: Tuple[float, float, float, float]
                      ) -> Optional[Dict[str, Tuple[float, float]]]:
        x1, y1, x2, y2 = [int(max(0, v)) for v in player_bbox]
        x2 = min(x2, frame.shape[1] - 1)
        y2 = min(y2, frame.shape[0] - 1)

        if x2 <= x1 or y2 <= y1:
            return None

        crop = frame[y1:y2, x1:x2]
        if crop.size == 0:
            return None

        rgb_crop = crop[:, :, ::-1]
        result = self._pose.process(rgb_crop)

        if result.pose_landmarks is None:
            return None

        landmarks = result.pose_landmarks.landmark
        crop_h, crop_w = crop.shape[:2]

        left = landmarks[self.LEFT_FOOT_INDEX]
        right = landmarks[self.RIGHT_FOOT_INDEX]

        left_foot = (x1 + left.x * crop_w, y1 + left.y * crop_h)
        right_foot = (x1 + right.x * crop_w, y1 + right.y * crop_h)

        return {"left": left_foot, "right": right_foot}

    def extract_feet_for_all(self, frame: np.ndarray,
                              players: Dict[int, Detection]
                              ) -> Dict[int, Dict[str, Tuple[float, float]]]:
        """
        players : {track_id: Detection} des joueurs détectés sur cette frame.
        Retourne {track_id: {"left": (x,y), "right": (x,y)}} pour les
        joueurs où l'extraction a réussi.
        """
        results = {}
        for track_id, det in players.items():
            feet = self.extract_feet(frame, det.bbox)
            if feet is not None:
                results[track_id] = feet
        return results

    def close(self) -> None:
        self._pose.close()