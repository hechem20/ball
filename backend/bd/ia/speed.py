"""
speed.py
========
Module professionnel de suivi et d'analyse de vitesse des joueurs
pour un pipeline d'analyse football (YOLO + tracking + QVAC).

Fonctionnalités :
- Filtre de Kalman pour lisser la trajectoire de chaque joueur
- Calibration pixel -> mètre via homographie (4 points terrain connus)
- Calcul de la vitesse instantanée, moyenne, maximale
- Calcul de la distance totale parcourue
- Suivi multi-joueurs (un tracker indépendant par ID)
- Export JSON des statistiques
- Annotation vidéo (OpenCV) prête à l'emploi

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
except ImportError:  # OpenCV optionnel pour l'annotation vidéo
    cv2 = None


# ---------------------------------------------------------------------------
# 1. FILTRE DE KALMAN (position + vitesse, modèle à vitesse constante)
# ---------------------------------------------------------------------------

class KalmanPositionFilter:
    """
    Filtre de Kalman 2D simple, état = [x, y, vx, vy].
    Modèle à vitesse constante, utilisé pour lisser les positions bruitées
    issues de la détection (YOLO / tracker).
    """

    def __init__(self, dt: float = 1 / 30, process_noise: float = 1.0,
                 measurement_noise: float = 5.0):
        self.dt = dt

        # Vecteur d'état [x, y, vx, vy]
        self.x = np.zeros((4, 1), dtype=np.float64)

        # Matrice de transition d'état
        self.F = np.array([
            [1, 0, dt, 0],
            [0, 1, 0, dt],
            [0, 0, 1, 0],
            [0, 0, 0, 1],
        ], dtype=np.float64)

        # Matrice d'observation (on observe seulement x, y)
        self.H = np.array([
            [1, 0, 0, 0],
            [0, 1, 0, 0],
        ], dtype=np.float64)

        # Covariance du bruit de processus
        q = process_noise
        self.Q = np.array([
            [q, 0, 0, 0],
            [0, q, 0, 0],
            [0, 0, q, 0],
            [0, 0, 0, q],
        ], dtype=np.float64)

        # Covariance du bruit de mesure
        r = measurement_noise
        self.R = np.array([
            [r, 0],
            [0, r],
        ], dtype=np.float64)

        # Covariance d'erreur d'estimation
        self.P = np.eye(4) * 500.0

        self.initialized = False

    def init(self, x: float, y: float) -> None:
        self.x = np.array([[x], [y], [0.0], [0.0]], dtype=np.float64)
        self.P = np.eye(4) * 500.0
        self.initialized = True

    def predict(self) -> Tuple[float, float, float, float]:
        self.x = self.F @ self.x
        self.P = self.F @ self.P @ self.F.T + self.Q
        return tuple(self.x.flatten())

    def update(self, x: float, y: float) -> Tuple[float, float, float, float]:
        if not self.initialized:
            self.init(x, y)
            return tuple(self.x.flatten())

        z = np.array([[x], [y]], dtype=np.float64)
        y_err = z - (self.H @ self.x)
        S = self.H @ self.P @ self.H.T + self.R
        K = self.P @ self.H.T @ np.linalg.inv(S)

        self.x = self.x + K @ y_err
        self.P = (np.eye(4) - K @ self.H) @ self.P

        return tuple(self.x.flatten())

    @property
    def position(self) -> Tuple[float, float]:
        return float(self.x[0, 0]), float(self.x[1, 0])

    @property
    def velocity_px(self) -> Tuple[float, float]:
        return float(self.x[2, 0]), float(self.x[3, 0])


# ---------------------------------------------------------------------------
# 2. CALIBRATION TERRAIN (pixel -> mètre)
# ---------------------------------------------------------------------------

class FieldCalibrator:
    """
    Calcule une homographie entre les coordonnées image (pixels) et les
    coordonnées réelles du terrain (mètres), à partir de 4 points connus
    (typiquement les coins du terrain ou des points de la surface de
    réparation).
    """

    def __init__(self, image_points: List[Tuple[float, float]],
                 real_points: List[Tuple[float, float]]):
        if len(image_points) != 4 or len(real_points) != 4:
            raise ValueError("4 points image et 4 points réels sont requis.")

        if cv2 is None:
            raise ImportError("OpenCV est requis pour la calibration (homographie).")

        src = np.array(image_points, dtype=np.float64)
        dst = np.array(real_points, dtype=np.float64)

        self.H, _ = cv2.findHomography(src, dst, method=0)

    def pixel_to_meter(self, x: float, y: float) -> Tuple[float, float]:
        point = np.array([x, y, 1.0], dtype=np.float64)
        mapped = self.H @ point
        mapped /= mapped[2]
        return float(mapped[0]), float(mapped[1])

    @staticmethod
    def default_ratio(pixels_per_meter: float):
        """
        Calibration simplifiée si aucune homographie n'est disponible :
        conversion linéaire à partir d'un ratio pixels/mètre mesuré
        manuellement sur une image de référence.
        """
        return LinearCalibrator(pixels_per_meter)


class LinearCalibrator:
    """Calibration simplifiée (fallback) : un seul ratio px/m global."""

    def __init__(self, pixels_per_meter: float):
        self.ratio = pixels_per_meter

    def pixel_to_meter(self, x: float, y: float) -> Tuple[float, float]:
        return x / self.ratio, y / self.ratio


# ---------------------------------------------------------------------------
# 3. SUIVI D'UN JOUEUR (historique, vitesse, distance)
# ---------------------------------------------------------------------------

@dataclass
class SpeedSample:
    frame_index: int
    timestamp: float
    x_m: float
    y_m: float
    instant_speed_kmh: float


@dataclass
class PlayerTrack:
    """
    Représente l'historique de suivi d'un joueur unique (identifié par
    un ID de tracker : ByteTrack, DeepSORT, etc.).
    """
    player_id: int
    dt: float = 1 / 30

    kalman: KalmanPositionFilter = field(default_factory=KalmanPositionFilter)

    positions_m: deque = field(default_factory=lambda: deque(maxlen=600))
    samples: List[SpeedSample] = field(default_factory=list)

    total_distance_m: float = 0.0
    max_speed_kmh: float = 0.0

    _last_point_m: Optional[Tuple[float, float]] = None
    _speed_buffer: deque = field(default_factory=lambda: deque(maxlen=5))

    def update(self, x_px: float, y_px: float, calibrator,
               frame_index: int, timestamp: Optional[float] = None) -> SpeedSample:
        """
        Met à jour le tracker avec une nouvelle détection (pixels),
        renvoie l'échantillon de vitesse pour cette frame.
        """
        if timestamp is None:
            timestamp = frame_index * self.dt

        # Lissage Kalman en pixels
        fx, fy, _, _ = self.kalman.update(x_px, y_px)

        # Conversion en mètres
        x_m, y_m = calibrator.pixel_to_meter(fx, fy)

        instant_speed_kmh = 0.0

        if self._last_point_m is not None:
            dist = math.hypot(x_m - self._last_point_m[0],
                               y_m - self._last_point_m[1])

            # Filtrage des sauts aberrants (erreurs de détection/ré-identification)
            max_plausible_dist = 12.0 * self.dt  # ~ 43 km/h max plausible entre 2 frames
            if dist <= max_plausible_dist:
                self.total_distance_m += dist
                speed_m_s = dist / self.dt
                instant_speed_kmh = speed_m_s * 3.6

        self._speed_buffer.append(instant_speed_kmh)
        smoothed_speed = sum(self._speed_buffer) / len(self._speed_buffer)

        self.max_speed_kmh = max(self.max_speed_kmh, smoothed_speed)
        self._last_point_m = (x_m, y_m)
        self.positions_m.append((x_m, y_m))

        sample = SpeedSample(
            frame_index=frame_index,
            timestamp=timestamp,
            x_m=x_m,
            y_m=y_m,
            instant_speed_kmh=round(smoothed_speed, 2),
        )
        self.samples.append(sample)
        return sample

    # ---- Statistiques agrégées -------------------------------------------------

    @property
    def average_speed_kmh(self) -> float:
        if not self.samples:
            return 0.0
        speeds = [s.instant_speed_kmh for s in self.samples]
        return round(sum(speeds) / len(speeds), 2)

    @property
    def duration_s(self) -> float:
        if len(self.samples) < 2:
            return 0.0
        return self.samples[-1].timestamp - self.samples[0].timestamp

    def summary(self) -> dict:
        return {
            "player_id": self.player_id,
            "total_distance_m": round(self.total_distance_m, 1),
            "average_speed_kmh": self.average_speed_kmh,
            "max_speed_kmh": round(self.max_speed_kmh, 2),
            "duration_s": round(self.duration_s, 1),
            "samples_count": len(self.samples),
        }


# ---------------------------------------------------------------------------
# 4. GESTIONNAIRE MULTI-JOUEURS
# ---------------------------------------------------------------------------

class SpeedAnalyzer:
    """
    Point d'entrée principal du module.
    Gère un ensemble de PlayerTrack (un par joueur détecté) et centralise
    la calibration, la mise à jour par frame, et l'export des résultats.
    """

    def __init__(self, calibrator, fps: float = 30.0):
        self.calibrator = calibrator
        self.fps = fps
        self.dt = 1.0 / fps
        self.tracks: Dict[int, PlayerTrack] = {}
        self.frame_index = 0

    def _get_or_create_track(self, player_id: int) -> PlayerTrack:
        if player_id not in self.tracks:
            self.tracks[player_id] = PlayerTrack(player_id=player_id, dt=self.dt)
        return self.tracks[player_id]

    def update_frame(self, detections: List[Tuple[int, float, float]],
                      timestamp: Optional[float] = None) -> Dict[int, SpeedSample]:
        """
        detections : liste de tuples (player_id, x_px, y_px) pour la frame courante.
        Retourne un dict {player_id: SpeedSample} pour affichage/export.
        """
        results = {}
        for player_id, x_px, y_px in detections:
            track = self._get_or_create_track(player_id)
            sample = track.update(x_px, y_px, self.calibrator,
                                   self.frame_index, timestamp)
            results[player_id] = sample

        self.frame_index += 1
        return results

    def get_summary(self) -> List[dict]:
        return [track.summary() for track in self.tracks.values()]

    def export_json(self, path: str) -> None:
        data = {
            "generated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            "fps": self.fps,
            "players": self.get_summary(),
        }
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    # ---- Annotation vidéo (OpenCV) ---------------------------------------------

    def annotate_frame(self, frame, detections_px: Dict[int, Tuple[float, float]]):
        """
        Dessine sur la frame la vitesse instantanée de chaque joueur suivi.
        detections_px : {player_id: (x_px, y_px)} positions brutes pour cette frame.
        """
        if cv2 is None:
            raise ImportError("OpenCV est requis pour l'annotation vidéo.")

        for player_id, (x_px, y_px) in detections_px.items():
            track = self.tracks.get(player_id)
            if track is None or not track.samples:
                continue

            speed = track.samples[-1].instant_speed_kmh
            label = f"ID {player_id} | {speed:.1f} km/h"

            cv2.circle(frame, (int(x_px), int(y_px)), 6, (0, 255, 0), -1)
            cv2.putText(
                frame, label, (int(x_px) + 10, int(y_px) - 10),
                cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 255, 255), 2,
            )

        return frame


