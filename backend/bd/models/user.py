print(f"🔍 CHARGEMENT MODULE: __name__={__name__}, __file__={__file__}")
from datetime import datetime
from enum import Enum
from sqlalchemy import String, DateTime, Boolean, Enum as SQLEnum, Float, Column, Integer
from sqlalchemy.orm import relationship
import uuid
from . import db

class UserRole(Enum):
    PLAYER = "player"
    COACH = "coach"
    ADMIN = "admin"

class User(db.Model):
    __tablename__ = 'users'
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    full_name = Column(String(100), nullable=False)
    email = Column(String(100), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    phone = Column(String(20), nullable=True)
    role = Column(SQLEnum(UserRole), nullable=False)
    experience = Column(String(50), nullable=True)
    is_verified = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    wallet_balance = Column(Float, default=100.0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relations
    club = relationship('CoachClub', back_populates='coach', uselist=False)
    trainings = relationship('TrainingSession', back_populates='player', lazy='dynamic')
    transactions = relationship('Transaction', back_populates='user', lazy='dynamic')
    
    def to_dict(self):
        return {
            'id': self.id,
            'full_name': self.full_name,
            'email': self.email,
            'phone': self.phone,
            'role': self.role.value if self.role else None,
            'experience': self.experience,
            'is_verified': self.is_verified,
            'is_active': self.is_active,
            'wallet_balance': self.wallet_balance,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }
    
    def __repr__(self):
        return f'<User {self.email}>'
