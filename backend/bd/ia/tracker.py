"""
tracker.py
==========
Suivi multi-objets simplifié : associe un ID persistant à chaque joueur
détecté d'une frame à l'autre, en se basant sur la proximité spatiale
(algorithme glouton du plus proche voisin).

Pour un usage en production, remplace ce tracker par ByteTrack ou
DeepSORT (bien plus robuste aux occlusions et croisements de joueurs).
Ce module fournit une implémentation autonome, sans dépendance externe,
suffisante pour un prototype ou une démo de hackathon.

Dépendances : numpy
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

from ia.detector import Detection


@dataclass
class TrackedObject:
    track_id: int
    bbox: Tuple[float, float, float, float]
    last_seen_frame: int
    missed_frames: int = 0


class SimpleTracker:
    """
    Tracker glouton par distance : à chaque frame, associe chaque nouvelle
    détection au track existant le plus proche (sous un seuil de distance),
    sinon crée un nouveau track. Les tracks non vus pendant plus de
    `max_missed_frames` sont supprimés.
    """

    def __init__(self, max_distance_px: float = 80.0, max_missed_frames: int = 15):
        self.max_distance_px = max_distance_px
        self.max_missed_frames = max_missed_frames

        self.tracks: Dict[int, TrackedObject] = {}
        self._next_id = 1
        self.frame_index = 0

    def update(self, detections: List[Detection]) -> Dict[int, Detection]:
        """
        Met à jour les tracks avec les détections de la frame courante.
        Retourne un dict {track_id: Detection} pour cette frame.
        """
        self.frame_index += 1
        assigned: Dict[int, Detection] = {}
        used_detection_indices = set()

        # Étape 1 : associer chaque track existant à la détection la plus proche disponible
        for track_id, track in list(self.tracks.items()):
            best_idx = None
            best_dist = float("inf")

            for idx, det in enumerate(detections):
                if idx in used_detection_indices:
                    continue
                dist = self._center_distance(track.bbox, det.bbox)
                if dist < best_dist:
                    best_dist = dist
                    best_idx = idx

            if best_idx is not None and best_dist <= self.max_distance_px:
                det = detections[best_idx]
                track.bbox = det.bbox
                track.last_seen_frame = self.frame_index
                track.missed_frames = 0
                used_detection_indices.add(best_idx)
                assigned[track_id] = det
            else:
                track.missed_frames += 1

        # Étape 2 : créer de nouveaux tracks pour les détections non assignées
        for idx, det in enumerate(detections):
            if idx in used_detection_indices:
                continue
            new_id = self._next_id
            self._next_id += 1
            self.tracks[new_id] = TrackedObject(
                track_id=new_id, bbox=det.bbox,
                last_seen_frame=self.frame_index, missed_frames=0,
            )
            assigned[new_id] = det

        # Étape 3 : supprimer les tracks perdus depuis trop longtemps
        stale_ids = [tid for tid, t in self.tracks.items()
                     if t.missed_frames > self.max_missed_frames]
        for tid in stale_ids:
            del self.tracks[tid]

        return assigned

    @staticmethod
    def _center_distance(bbox1: Tuple[float, float, float, float],
                          bbox2: Tuple[float, float, float, float]) -> float:
        c1 = ((bbox1[0] + bbox1[2]) / 2, (bbox1[1] + bbox1[3]) / 2)
        c2 = ((bbox2[0] + bbox2[2]) / 2, (bbox2[1] + bbox2[3]) / 2)
        return math.hypot(c1[0] - c2[0], c1[1] - c2[1])