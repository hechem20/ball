from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List
from .training import TrainingType, SkillLevel

@dataclass
class PlayerStats:
    player_id: str
    player_name: str
    email: str
    phone: str
    joined_date: datetime
    speed_score: float
    control_ball_score: float
    shoot_score: float
    pass_score: float
    total_score: float
    total_rewards: float
    training_sessions_count: int
    best_scores: Dict[TrainingType, float]
    sessions_count: Dict[TrainingType, int]
    overall_level: SkillLevel
    progress_rate: float
    
    def to_dict(self):
        return {
            'playerId': self.player_id,
            'playerName': self.player_name,
            'email': self.email,
            'phone': self.phone,
            'joinedDate': self.joined_date.isoformat(),
            'speedScore': self.speed_score,
            'controlBallScore': self.control_ball_score,
            'shootScore': self.shoot_score,
            'passScore': self.pass_score,
            'totalScore': self.total_score,
            'totalRewards': self.total_rewards,
            'trainingSessionsCount': self.training_sessions_count,
            'bestScores': {k.value: v for k, v in self.best_scores.items()},
            'sessionsCount': {k.value: v for k, v in self.sessions_count.items()},
            'overallLevel': self.overall_level.value,
            'progressRate': self.progress_rate
        }