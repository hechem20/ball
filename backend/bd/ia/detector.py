"""
detector.py
===========
Détection des objets (ballon, joueurs) sur chaque frame vidéo à l'aide
d'un modèle YOLO (Ultralytics).

Ce module isole toute la logique de détection brute : le reste du
pipeline (tracker.py, main.py) ne manipule que des objets Detection,
indépendamment du modèle utilisé en interne.

Dépendances : ultralytics, opencv-python, numpy
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Tuple

import numpy as np

try:
    from ultralytics import YOLO
except ImportError:
    YOLO = None


@dataclass
class Detection:
    """Une détection brute pour une frame donnée."""
    class_name: str          # "ball" ou "player"
    bbox: Tuple[float, float, float, float]  # x1, y1, x2, y2 en pixels
    confidence: float

    @property
    def center(self) -> Tuple[float, float]:
        x1, y1, x2, y2 = self.bbox
        return (x1 + x2) / 2, (y1 + y2) / 2

    @property
    def bottom_center(self) -> Tuple[float, float]:
        """Point au sol approximatif (utile pour la position réelle du joueur)."""
        x1, y1, x2, y2 = self.bbox
        return (x1 + x2) / 2, y2


class FootballDetector:
    """
    Wrapper autour d'un modèle YOLO entraîné (ou fine-tuné) pour détecter
    le ballon et les joueurs sur des images de match de football.

    Le modèle attendu doit exposer au moins deux classes : "ball" et
    "player" (adapter model_classes si ton modèle utilise des noms/index
    différents, par exemple un modèle YOLO11 fine-tuné sur un dataset
    football comme SoccerNet).
    """

    def __init__(self, model_path: str = "yolo11n.pt",
                 confidence_threshold: float = 0.35,
                 ball_class_names: Optional[List[str]] = None,
                 player_class_names: Optional[List[str]] = None):
        if YOLO is None:
            raise ImportError(
                "Le package 'ultralytics' est requis. Installe-le avec : "
                "pip install ultralytics"
            )

        self.model = YOLO(model_path)
        self.confidence_threshold = confidence_threshold

        self.ball_class_names = ball_class_names or ["ball", "sports ball"]
        self.player_class_names = player_class_names or ["player", "person"]

    def detect(self, frame: np.ndarray) -> List[Detection]:
        """
        Lance l'inférence sur une frame et renvoie la liste des détections
        pertinentes (ballon + joueurs), filtrées par seuil de confiance.
        """
        results = self.model.predict(
            source=frame, conf=self.confidence_threshold, verbose=False,
        )

        detections: List[Detection] = []
        if not results:
            return detections

        result = results[0]
        names = result.names

        for box in result.boxes:
            cls_id = int(box.cls[0])
            cls_name = names.get(cls_id, str(cls_id)) if isinstance(names, dict) else names[cls_id]
            confidence = float(box.conf[0])
            x1, y1, x2, y2 = [float(v) for v in box.xyxy[0]]

            if cls_name in self.ball_class_names:
                label = "ball"
            elif cls_name in self.player_class_names:
                label = "player"
            else:
                continue

            detections.append(Detection(
                class_name=label,
                bbox=(x1, y1, x2, y2),
                confidence=confidence,
            ))

        return detections

    def detect_ball(self, frame: np.ndarray) -> Optional[Detection]:
        """Renvoie la détection de ballon la plus confiante, ou None."""
        detections = [d for d in self.detect(frame) if d.class_name == "ball"]
        if not detections:
            return None
        return max(detections, key=lambda d: d.confidence)

    def detect_players(self, frame: np.ndarray) -> List[Detection]:
        return [d for d in self.detect(frame) if d.class_name == "player"]