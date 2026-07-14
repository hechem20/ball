from datetime import datetime
from sqlalchemy import String, DateTime, Boolean, Float, Integer, JSON, Column, ForeignKey
from sqlalchemy.orm import relationship
import uuid
from . import db

class CoachClub(db.Model):
    __tablename__ = 'coach_clubs'
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    coach_id = Column(String(36), ForeignKey('users.id'), unique=True, nullable=False, index=True)
    club_name = Column(String(100), nullable=False)
    description = Column(String(500), nullable=True)
    logo_url = Column(String(255), nullable=True)
    budget = Column(Float, default=0.0)
    subscription_fee = Column(Float, default=0.0)
    max_players = Column(Integer, default=20)
    current_players = Column(JSON, default=list)
    specialties = Column(JSON, default=list)
    rating = Column(Float, default=0.0)
    total_players = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relations
    coach = relationship('User', back_populates='club')
    
    def to_dict(self):
        current_players = self.current_players or []
        return {
            'id': self.id,
            'coach_id': self.coach_id,
            'coach_name': self.coach.full_name if self.coach else '',
            'club_name': self.club_name,
            'description': self.description,
            'logo_url': self.logo_url,
            'budget': self.budget,
            'subscription_fee': self.subscription_fee,
            'max_players': self.max_players,
            'current_players': current_players,
            'specialties': self.specialties or [],
            'rating': self.rating,
            'total_players': self.total_players,
            'is_active': self.is_active,
            'available_slots': self.max_players - len(current_players),
            'has_available_slots': len(current_players) < self.max_players,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }
    
    def update_current_players(self):
        self.current_players = self.current_players or []
        self.total_players = len(self.current_players)
    
    def __repr__(self):
        return f'<CoachClub {self.club_name}>'