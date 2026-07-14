from datetime import datetime
from enum import Enum
from sqlalchemy import String, DateTime, Float, ForeignKey, Enum as SQLEnum, Column
from sqlalchemy.orm import relationship
import uuid
from . import db

class TransactionStatus(Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    REFUNDED = "refunded"

class TransactionType(Enum):
    PAYMENT = "payment"
    REWARD = "reward"
    REFUND = "refund"

class Transaction(db.Model):
    __tablename__ = 'transactions'
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey('users.id'), nullable=False, index=True)
    coach_id = Column(String(36), nullable=True)
    club_id = Column(String(36), nullable=True)
    amount = Column(Float, nullable=False)
    type = Column(SQLEnum(TransactionType), nullable=False)
    status = Column(SQLEnum(TransactionStatus), default=TransactionStatus.PENDING)
    description = Column(String(200), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relations
    user = relationship('User', back_populates='transactions')
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'coach_id': self.coach_id,
            'club_id': self.club_id,
            'amount': self.amount,
            'type': self.type.value if self.type else None,
            'status': self.status.value if self.status else None,
            'description': self.description,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }
    
    def __repr__(self):
        return f'<Transaction {self.id} - {self.type}>'