"""
main.py
=======
Pipeline complet d'analyse DYNAMIQUE d'une vidéo de football.

Contrairement aux exemples de speed.py / control.py / pass.py / shoot.py
(qui utilisaient des données simulées pour démontrer chaque module
isolément), ce script traite une vraie vidéo, frame par frame, en
temps réel ou en différé :

    Vidéo (.mp4)
        │
        ▼
    FootballDetector   -> détecte ballon + joueurs (YOLO)
        │
        ▼
    SimpleTracker       -> attribue un ID persistant à chaque joueur
        │
        ▼
    FeetExtractor        -> localise les pieds de chaque joueur (MediaPipe)
        │
        ▼
    SpeedAnalyzer / BallControlAnalyzer / PassAnalyzer / ShootAnalyzer
        │
        ▼
    Vidéo annotée (.mp4) + rapports JSON

Usage :
    python main.py --video match.mp4 --output annotated.mp4 --model yolo11n.pt

Dépendances : ultralytics, mediapipe, opencv-python, numpy
"""

from __future__ import annotations

import argparse
import time
from typing import Dict, Optional, Tuple

import cv2
import numpy as np

from ia.detector import FootballDetector, Detection

from ia.speed import SpeedAnalyzer, LinearCalibrator
from ia.control import BallControlAnalyzer, ControlConfig
from ia.tracker import SimpleTracker
from ia.pose import FeetExtractor

from ia.passe import PassAnalyzer, PassConfig
from ia.shoot import ShootAnalyzer, ShootConfig


class FootballVideoPipeline:
    def __init__(self, model_path: str, fps: float,
                 pixels_per_meter: float = 25.0,
                 ball_tracker_dt: Optional[float] = None):
        self.detector = FootballDetector(model_path=model_path)
        self.player_tracker = SimpleTracker()

        self.feet_extractor = FeetExtractor()

        calibrator = LinearCalibrator(pixels_per_meter=pixels_per_meter)

        self.speed_analyzer = SpeedAnalyzer(calibrator=calibrator, fps=fps)
        self.control_analyzer = BallControlAnalyzer(config=ControlConfig(), fps=fps)
        self.pass_analyzer = PassAnalyzer(config=PassConfig(), fps=fps)
        self.shoot_analyzer = ShootAnalyzer(config=ShootConfig(), fps=fps)

        self.calibrator = calibrator
        self.fps = fps
        self.frame_index = 0

    def process_frame(self, frame: np.ndarray) -> np.ndarray:
        self.frame_index += 1

        detections = self.detector.detect(frame)
        ball_det = next((d for d in detections if d.class_name == "ball"), None)
        player_dets = [d for d in detections if d.class_name == "player"]

        tracked_players: Dict[int, Detection] = self.player_tracker.update(player_dets)

        # --- Vitesse par joueur -------------------------------------------------
        speed_detections = [
            (track_id, *det.bottom_center) for track_id, det in tracked_players.items()
        ]
        speed_results = self.speed_analyzer.update_frame(speed_detections)

        # --- Pieds (pour le contrôle de balle) -----------------------------------
        feet_by_player = self.feet_extractor.extract_feet_for_all(frame, tracked_players)

        control_result = None
        ball_pos_m = None
        controller_id = None

        if ball_det is not None and feet_by_player:
            control_result = self.control_analyzer.update_frame(
                ball_bbox=ball_det.bbox, players_feet=feet_by_player,
            )
            if control_result is not None:
                controller_id = control_result.get("controller_id")
                ball_pos_px = control_result["ball_position"]
                ball_pos_m = self.calibrator.pixel_to_meter(*ball_pos_px)
        elif ball_det is not None:
            # Pas de pieds détectés cette frame : on met au moins à jour
            # la position ballon pour la passe/le tir
            bx, by = ball_det.center
            ball_pos_m = self.calibrator.pixel_to_meter(bx, by)

        # --- Passes ---------------------------------------------------------------
        pass_event = self.pass_analyzer.update_frame(ball_pos_m, controller_id)

        # --- Tirs -------------------------------------------------------------------
        shot_event = self.shoot_analyzer.update_frame(ball_pos_m, controller_id)

        # --- Annotation ---------------------------------------------------------------
        annotated = frame

        for track_id, det in tracked_players.items():
            x1, y1, x2, y2 = [int(v) for v in det.bbox]
            cv2.rectangle(annotated, (x1, y1), (x2, y2), (255, 200, 0), 2)
            speed_sample = speed_results.get(track_id)
            label = f"ID {track_id}"
            if speed_sample:
                label += f" | {speed_sample.instant_speed_kmh:.1f} km/h"
            cv2.putText(annotated, label, (x1, y1 - 8),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 200, 0), 2)

        if ball_det is not None:
            bx1, by1, bx2, by2 = [int(v) for v in ball_det.bbox]
            cv2.rectangle(annotated, (bx1, by1), (bx2, by2), (0, 255, 255), 2)

        annotated = self.control_analyzer.annotate_frame(annotated, control_result)
        if pass_event is not None:
            annotated = self.pass_analyzer.annotate_frame(annotated, pass_event)
        if shot_event is not None:
            annotated = self.shoot_analyzer.annotate_frame(annotated, shot_event)

        return annotated

    def export_reports(self, output_prefix: str = "report") -> None:
        self.speed_analyzer.export_json(f"{output_prefix}_speed.json")
        self.control_analyzer.export_json(f"{output_prefix}_control.json")
        self.pass_analyzer.export_json(f"{output_prefix}_pass.json")
        self.shoot_analyzer.export_json(f"{output_prefix}_shoot.json")

    def close(self) -> None:
        self.feet_extractor.close()


def run(video_path: str, output_path: str, model_path: str,
        pixels_per_meter: float, max_frames: Optional[int] = None) -> None:
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise FileNotFoundError(f"Impossible d'ouvrir la vidéo : {video_path}")

    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    writer = cv2.VideoWriter(output_path, fourcc, fps, (width, height))

    pipeline = FootballVideoPipeline(
        model_path=model_path, fps=fps, pixels_per_meter=pixels_per_meter,
    )

    start_time = time.time()
    frame_count = 0

    print(f"Analyse en cours : {video_path} ({width}x{height} @ {fps:.1f} fps)")

    while True:
        ok, frame = cap.read()
        if not ok:
            break

        annotated = pipeline.process_frame(frame)
        writer.write(annotated)

        frame_count += 1
        if frame_count % 100 == 0:
            elapsed = time.time() - start_time
            print(f"  {frame_count} frames traitées ({frame_count / elapsed:.1f} fps de traitement)")

        if max_frames is not None and frame_count >= max_frames:
            break

    cap.release()
    writer.release()
    pipeline.close()

    pipeline.export_reports(output_prefix="report")

    total_time = time.time() - start_time
    print(f"\nTerminé : {frame_count} frames en {total_time:.1f}s "
          f"({frame_count / total_time:.1f} fps moyen)")
    print(f"Vidéo annotée : {output_path}")
    print("Rapports JSON : report_speed.json, report_control.json, "
          "report_pass.json, report_shoot.json")


if __name__ == "__main__":

    parser = argparse.ArgumentParser(
        description="Analyse dynamique football"
    )

    parser.add_argument(
        "--video",
        required=True
    )

    parser.add_argument(
        "--output",
        default="annotated.mp4"
    )

    parser.add_argument(
        "--model",
        default="yolo11n.pt"
    )

    args = parser.parse_args()


    run(
        video_path=args.video,
        output_path=args.output,
        model_path=args.model,
        pixels_per_meter=25.0
    )