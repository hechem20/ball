import bcrypt
import uuid
from datetime import datetime
from flask_jwt_extended import create_access_token, create_refresh_token
from models import db, User, UserRole

class AuthService:
    @staticmethod
    def hash_password(password):
        """Hash un mot de passe avec bcrypt"""
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')
    
    @staticmethod
    def verify_password(password, password_hash):
        """Vérifie un mot de passe"""
        return bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))
    
    @staticmethod
    def create_user(data):
        """Crée un nouvel utilisateur"""
        # Vérifier si l'email existe déjà
        existing_user = User.query.filter_by(email=data['email']).first()
        if existing_user:
            raise ValueError("Cet email est déjà utilisé")
        
        # Créer l'utilisateur
        user = User(
            id=str(uuid.uuid4()),
            full_name=data['full_name'],
            email=data['email'],
            password_hash=AuthService.hash_password(data['password']),
            phone=data.get('phone', ''),
            role=UserRole(data['role']),
            experience=data.get('experience'),
            wallet_balance=100.0  # Bonus d'inscription
        )
        
        db.session.add(user)
        db.session.commit()
        
        # Créer les tokens
        access_token = create_access_token(identity=user.id)
        refresh_token = create_refresh_token(identity=user.id)
        
        return user, access_token, refresh_token
    
    @staticmethod
    def login_user(email, password):
        """Authentifie un utilisateur"""
        user = User.query.filter_by(email=email).first()
        if not user:
            raise ValueError("Email ou mot de passe incorrect")
        
        if not AuthService.verify_password(password, user.password_hash):
            raise ValueError("Email ou mot de passe incorrect")
        
        if not user.is_active:
            raise ValueError("Compte désactivé")
        
        # Créer les tokens
        access_token = create_access_token(identity=user.id)
        refresh_token = create_refresh_token(identity=user.id)
        
        return user, access_token, refresh_token
    
    @staticmethod
    def get_user_by_id(user_id):
        return User.query.get(user_id)
    
    @staticmethod
    def update_user(user_id, data):
        user = User.query.get(user_id)
        if not user:
            raise ValueError("Utilisateur non trouvé")
        
        if 'full_name' in data:
            user.full_name = data['full_name']
        if 'phone' in data:
            user.phone = data['phone']
        if 'experience' in data:
            user.experience = data['experience']
        
        db.session.commit()
        return user
    
    @staticmethod
    def update_wallet(user_id, amount):
        user = User.query.get(user_id)
        if not user:
            raise ValueError("Utilisateur non trouvé")
        
        user.wallet_balance += amount
        db.session.commit()
        return user.wallet_balance