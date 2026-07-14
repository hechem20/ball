"""
backend/analysis_service.py
============================
Service d'IA branché sur le VRAI pipeline vidéo football (YOLO +
MediaPipe + speed/control/passing/shoot), tout en conservant l'interface
attendue par les routes Flask existantes (routes.py) :

    ai_service = AIService()
    analysis = ai_service.analyze_training(training_type, video_path)

-> dict { score, feedback, metrics, level, analysis_type, timestamp }

Remplace l'ancienne version basée sur TensorFlow/Keras (scores simulés
par un CNN non entraîné). Ici :
- si une vidéo existe -> analyse réelle via FootballVideoPipeline
- sinon -> analyse simulée de repli (pour ne pas casser les écrans qui
  appellent analyze_training sans vidéo)
"""

from __future__ import annotations

import os
import sys
import random
import tempfile
from datetime import datetime
from typing import Optional

import cv2

from models import TrainingType, SkillLevel

# Permet d'importer main.py (FootballVideoPipeline) et les modules du
# pipeline (detector.py, tracker.py, pose.py, speed.py, control.py,
# passing.py, shoot.py) situés au niveau du dossier parent de backend/.
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from main import FootballVideoPipeline  # noqa: E402


DEFAULT_MODEL_PATH = os.environ.get("FOOTBALL_YOLO_MODEL", "yolo11n.pt")
DEFAULT_PIXELS_PER_METER = float(os.environ.get("FOOTBALL_PX_PER_M", "25.0"))
DEFAULT_MAX_FRAMES = int(os.environ.get("FOOTBALL_MAX_FRAMES", "300"))  # ~10s à 30fps


# Associe chaque valeur possible de TrainingType.value (selon ton
# models.py) à la clé interne utilisée par le pipeline. Ajoute d'autres
# alias ici si ton enum utilise des libellés différents.
_TYPE_ALIASES = {
    "speed": "speed",
    "control_ball": "control",
    "control": "control",
    "pass": "pass",
    "shoot": "shoot",
}


def _resolve_type_key(training_type) -> str:

    if isinstance(training_type, str):
        raw = training_type.lower()
    else:
        raw = training_type.value.lower()

    return _TYPE_ALIASES.get(raw, raw)


class AIService:
    """Analyse réelle (vidéo -> YOLO/MediaPipe) avec repli simulé."""

    def __init__(self):
        pass  # le pipeline YOLO est instancié à la demande (par analyse), pas au démarrage

    # ------------------------------------------------------------------
    # API PUBLIQUE (utilisée par routes.py)
    # ------------------------------------------------------------------

    def analyze_training(self, training_type: "TrainingType", video_path: str = None) -> dict:
        try:
            if video_path and os.path.exists(video_path):
                return self._analyze_with_video(video_path, training_type)
            return self._analyze_without_video(training_type)
        except Exception as e:
            print(f"❌ Erreur d'analyse: {e}")
            return self._fallback_analysis(training_type)

    def analyze_video_file(self, video_file) -> dict:
        """Analyse un fichier vidéo uploadé (objet fichier Flask/Werkzeug)."""
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as tmp:
                tmp.write(video_file.read())
                tmp_path = tmp.name
            result = self._analyze_with_video(tmp_path, TrainingType.CONTROL_BALL)
            os.unlink(tmp_path)
            return result
        except Exception as e:
            print(f"❌ Erreur analyse vidéo fichier: {e}")
            return self._fallback_analysis(TrainingType.CONTROL_BALL)

    def get_skill_level(self, score: float) -> "SkillLevel":
        if score >= 90:
            return SkillLevel.EXPERT
        elif score >= 75:
            return SkillLevel.ADVANCED
        elif score >= 50:
            return SkillLevel.INTERMEDIATE
        return SkillLevel.BEGINNER

    def calculate_reward(self, score: float, training_type: "TrainingType") -> float:
        base_reward = 1.0
        multiplier = score / 100
        type_bonus = {
            TrainingType.SPEED: 1.2,
            TrainingType.CONTROL_BALL: 1.0,
            TrainingType.SHOOT: 1.1,
            TrainingType.PASS: 0.9,
        }
        reward = base_reward * multiplier * 10 * type_bonus.get(training_type, 1.0)
        return round(min(max(reward, 0.5), 10.0), 2)

    def get_improvement_tips(self, training_type, score, metrics=None) -> list:
        tips = []
        if score < 60:
            tips += [
                "🎯 Augmentez la fréquence de vos entraînements (3-4 fois par semaine)",
                "📹 Enregistrez-vous pour analyser votre technique",
            ]
        specific = {
            "speed": ["🏃 Travaillez vos sprints sur 20-30 mètres", "💪 Renforcez vos jambes"],
            "control": ["⚽ Pratiquez le dribble en conduite de balle", "🎯 Travaillez la première touche"],
            "pass": ["🔄 Travaillez les passes courtes et longues", "🧠 Développez votre vision de jeu"],
            "shoot": ["🎯 Travaillez la précision avant la puissance", "📐 Variez les angles de tir"],
        }
        tips += specific.get(_resolve_type_key(training_type), [])
        return tips[:5]

    def analyze_image(self, image_data) -> dict:
        # Analyse d'une image isolée non couverte par le pipeline vidéo :
        # renvoie un résultat de repli plutôt qu'un score inventé.
        return self._fallback_analysis(TrainingType.CONTROL_BALL)

    # ------------------------------------------------------------------
    # ANALYSE RÉELLE (vidéo -> pipeline YOLO/MediaPipe)
    # ------------------------------------------------------------------

    def _analyze_with_video(self, video_path: str, training_type: "TrainingType") -> dict:
        type_key = _resolve_type_key(training_type)

        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            print("⚠️ Vidéo illisible, bascule sur analyse simulée")
            return self._analyze_without_video(training_type)

        fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
        pipeline = FootballVideoPipeline(
            model_path=DEFAULT_MODEL_PATH, fps=fps, pixels_per_meter=DEFAULT_PIXELS_PER_METER,
        )

        frame_count = 0
        try:
            while True:
                ok, frame = cap.read()
                if not ok:
                    break
                pipeline.process_frame(frame)
                frame_count += 1
                if DEFAULT_MAX_FRAMES and frame_count >= DEFAULT_MAX_FRAMES:
                    break
        finally:
            cap.release()
            pipeline.close()

        if frame_count == 0:
            return self._analyze_without_video(training_type)

        dispatch = {
            "speed": self._build_speed_result,
            "control": self._build_control_result,
            "pass": self._build_pass_result,
            "shoot": self._build_shoot_result,
        }
        builder = dispatch.get(type_key)
        if builder is None:
            return self._analyze_without_video(training_type)

        result = builder(pipeline)
        result["level"] = self.get_skill_level(result["score"]).value
        result["analysis_type"] = "video"
        result["frames_analyzed"] = frame_count
        result["timestamp"] = datetime.utcnow().isoformat()
        return result

    def _build_speed_result(self, pipeline: FootballVideoPipeline) -> dict:
        tracks = pipeline.speed_analyzer.tracks
        if not tracks:
            return self._no_detection_result("vitesse")
        dominant = max(tracks.values(), key=lambda t: len(t.samples))
        summary = dominant.summary()
        max_speed = summary["max_speed_kmh"]
        avg_speed = summary["average_speed_kmh"]
        score = min(100.0, (max_speed / 30.0) * 100.0)

        if score >= 85:
            feedback = f"Excellente pointe de vitesse ({max_speed:.1f} km/h) ! Continue sur cette lancée."
        elif score >= 60:
            feedback = f"Bon rythme ({max_speed:.1f} km/h). Travaille l'explosivité des premiers appuis."
        else:
            feedback = f"Vitesse de pointe mesurée : {max_speed:.1f} km/h. Fais des sprints courts et intenses."

        metrics = {
            "vitesse_max_kmh": round(max_speed, 1),
            "vitesse_moyenne": round(avg_speed, 1),
            "distance_totale": round(summary["total_distance_m"], 1),
            "repetitions": len(dominant.samples),
        }
        return {"score": round(score, 1), "feedback": feedback, "metrics": metrics}

    def _build_control_result(self, pipeline: FootballVideoPipeline) -> dict:
        players = pipeline.control_analyzer.players
        if not players:
            return self._no_detection_result("contrôle de balle")
        dominant_id = max(players, key=lambda pid: players[pid].total_frames_tracked)
        stats = players[dominant_id]
        score_data = pipeline.control_analyzer.control_score(dominant_id)
        score = score_data["overall"]

        if score >= 85:
            feedback = "Contrôle de balle très solide, le ballon reste proche de toi même sous pression."
        elif score >= 60:
            feedback = "Bon contrôle général. Travaille la première touche pour gagner en fluidité."
        else:
            feedback = "Le ballon s'éloigne souvent de toi. Travaille la conduite de balle à faible vitesse."

        metrics = {
            "possession": round(stats.possession_percent, 1),
            "touches": stats.touch_count,
            "dribbles": stats.dribble_count,
            "repetitions": stats.touch_count,
        }
        return {"score": round(score, 1), "feedback": feedback, "metrics": metrics}

    def _build_pass_result(self, pipeline: FootballVideoPipeline) -> dict:
        stats_by_player = pipeline.pass_analyzer.player_stats
        if not stats_by_player:
            return self._no_detection_result("passe")
        dominant_id = max(stats_by_player, key=lambda pid: stats_by_player[pid]["passes_attempted"])
        summary = pipeline.pass_analyzer.get_player_summary(dominant_id)
        if summary["passes_attempted"] == 0:
            return self._no_detection_result("passe")
        score = summary["accuracy_percent"]

        if score >= 85:
            feedback = "Excellente précision de passe, tu trouves régulièrement ton partenaire."
        elif score >= 60:
            feedback = "Passes globalement fiables. Travaille le dosage sur les longues distances."
        else:
            feedback = "Beaucoup de passes imprécises. Travaille la surface de contact et le pied d'appui."

        metrics = {
            "passes_tentees": summary["passes_attempted"],
            "passes_reussies": summary["passes_completed"],
            "precision": score,
            "distance_totale": round(summary["total_distance_m"], 1),
            "repetitions": summary["passes_attempted"],
        }
        return {"score": round(score, 1), "feedback": feedback, "metrics": metrics}

    def _build_shoot_result(self, pipeline: FootballVideoPipeline) -> dict:
        stats_by_player = pipeline.shoot_analyzer.player_stats
        if not stats_by_player:
            return self._no_detection_result("tir")
        dominant_id = max(stats_by_player, key=lambda pid: stats_by_player[pid]["shots"])
        summary = pipeline.shoot_analyzer.get_player_summary(dominant_id)
        if summary["shots"] == 0:
            return self._no_detection_result("tir")

        avg_xg = stats_by_player[dominant_id]["total_xg"] / summary["shots"]
        score = min(100.0, summary["accuracy_percent"] * 0.7 + avg_xg * 100 * 0.3)

        if score >= 85:
            feedback = "Frappes puissantes et bien cadrées, très bon taux de réussite."
        elif score >= 60:
            feedback = "Bonne base de frappe. Travaille la régularité du cadrage sous fatigue."
        else:
            feedback = "Beaucoup de tirs manquent le cadre. Ralentis la course d'élan."

        metrics = {
            "tirs": summary["shots"],
            "buts": summary["goals"],
            "cadrage": summary["accuracy_percent"],
            "xg_moyen": round(avg_xg, 2),
            "repetitions": summary["shots"],
        }
        return {"score": round(score, 1), "feedback": feedback, "metrics": metrics}

    def _no_detection_result(self, exercise_label: str) -> dict:
        return {
            "score": 0.0,
            "feedback": (
                f"Aucune donnée exploitable détectée pour l'exercice {exercise_label}. "
                "Filme de plus près, avec le ballon et le joueur bien visibles."
            ),
            "metrics": {},
        }

    # ------------------------------------------------------------------
    # ANALYSE SIMULÉE (repli quand aucune vidéo n'est fournie)
    # ------------------------------------------------------------------

    def _analyze_without_video(self, training_type: "TrainingType") -> dict:
        score = self._simulate_score()
        metrics = self._generate_metrics(training_type)
        feedback = self._generate_ai_feedback(score)
        level = self.get_skill_level(score)
        return {
            "score": round(float(score), 2),
            "feedback": feedback,
            "metrics": metrics,
            "level": level.value,
            "analysis_type": "simulated",
            "timestamp": datetime.utcnow().isoformat(),
        }

    def _simulate_score(self) -> float:
        score = random.normalvariate(70, 15)
        return max(0.0, min(100.0, score))

    def _generate_metrics(self, training_type: "TrainingType") -> dict:
        type_key = _resolve_type_key(training_type)
        metrics = {
            "speed": {
                "vitesse_max_kmh": round(20 + random.random() * 15, 1),
                "acceleration_ms2": round(5 + random.random() * 3, 1),
                "repetitions": random.randint(10, 25),
            },
            "control": {
                "precision_dribble": round(65 + random.random() * 30, 1),
                "controle_balle": round(60 + random.random() * 35, 1),
                "repetitions": random.randint(20, 35),
            },
            "shoot": {
                "puissance_tir": round(70 + random.random() * 25, 1),
                "precision_tir": round(55 + random.random() * 40, 1),
                "repetitions": random.randint(15, 30),
            },
            "pass": {
                "precision_passe": round(60 + random.random() * 35, 1),
                "vision_jeu": round(70 + random.random() * 25, 1),
                "repetitions": random.randint(25, 40),
            },
        }
        return metrics.get(type_key, {})

    def _generate_ai_feedback(self, score: float) -> str:
        if score >= 90:
            return "🏆 Excellent ! Technique impressionnante."
        elif score >= 75:
            return "💪 Très bon travail, continue sur ce rythme."
        elif score >= 50:
            return "📊 Bonne base, la régularité paiera."
        return "🎯 Continue à t'entraîner régulièrement, les progrès viendront."

    def _fallback_analysis(self, training_type: "TrainingType") -> dict:
        return {
            "score": 70.0,
            "feedback": "Analyse indisponible pour le moment. Continue tes efforts !",
            "metrics": {},
            "level": SkillLevel.INTERMEDIATE.value,
            "analysis_type": "fallback",
            "timestamp": datetime.utcnow().isoformat(),
        }


def initialize_ai_service() -> AIService:
    return AIService()