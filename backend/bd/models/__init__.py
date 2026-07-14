from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)

from .user import User, UserRole
from .club import CoachClub
from .training import TrainingSession, TrainingType, SkillLevel
from .transaction import Transaction, TransactionStatus, TransactionType
from .player_stats import PlayerStats

__all__ = [
    'db',
    'User',
    'UserRole',
    'CoachClub',
    'TrainingSession',
    'TrainingType',
    'SkillLevel',
    'Transaction',
    'TransactionStatus',
    'TransactionType',
    'PlayerStats'
]