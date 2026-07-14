from datetime import datetime
from enum import Enum
from sqlalchemy import String, DateTime, Float, JSON, Enum as SQLEnum, ForeignKey, Column
from sqlalchemy.orm import relationship
import uuid
from . import db

class TrainingType(Enum):
    SPEED = "speed"
    CONTROL_BALL = "control_ball"
    SHOOT = "shoot"
    PASS = "pass"

class SkillLevel(Enum):
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    EXPERT = "expert"

class TrainingSession(db.Model):
    __tablename__ = 'training_sessions'
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    player_id = Column(String(36), ForeignKey('users.id'), nullable=False, index=True)
    type = Column(SQLEnum(TrainingType), nullable=False)
    date = Column(DateTime, default=datetime.utcnow)
    score = Column(Float, nullable=False)
    duration = Column(Float, nullable=False)
    level = Column(SQLEnum(SkillLevel), nullable=False)
    reward = Column(Float, default=0.0)
    video_url = Column(String(255), nullable=True)
    ai_feedback = Column(String(500), nullable=True)
    metrics = Column(JSON, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relations
    player = relationship('User', back_populates='trainings')
    
    def to_dict(self):
        return {
            'id': self.id,
            'player_id': self.player_id,
            'type': self.type.value if self.type else None,
            'date': self.date.isoformat() if self.date else None,
            'score': self.score,
            'duration': self.duration,
            'level': self.level.value if self.level else None,
            'reward': self.reward,
            'video_url': self.video_url,
            'ai_feedback': self.ai_feedback,
            'metrics': self.metrics or {},
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }
    
    def __repr__(self):
        return f'<TrainingSession {self.id} - {self.type}>'