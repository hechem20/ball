from datetime import datetime
from sqlalchemy import desc, func
from models import db, CoachClub, User, UserRole
import uuid

class ClubService:
    @staticmethod
    def create_club(data):
        """Crée un nouveau club"""
        try:
            # Vérifier si le coach existe déjà
            existing_club = CoachClub.query.filter_by(coach_id=data['coach_id']).first()
            if existing_club:
                raise ValueError("Ce coach a déjà un club")
            
            club = CoachClub(
                coach_id=data['coach_id'],
                club_name=data['club_name'],
                description=data.get('description', ''),
                logo_url=data.get('logo_url', ''),
                budget=data.get('budget', 10000.0),
                subscription_fee=data.get('subscription_fee', 50.0),
                max_players=data.get('max_players', 30),
                specialties=data.get('specialties', ['Football', 'Tactique']),
                is_active=True
            )
            
            db.session.add(club)
            db.session.commit()
            return club
        except Exception as e:
            db.session.rollback()
            raise e
    
    @staticmethod
    def get_club_by_id(club_id):
        return CoachClub.query.get(club_id)
    
    @staticmethod
    def get_club_by_coach_id(coach_id):
        return CoachClub.query.filter_by(coach_id=coach_id).first()
    
    @staticmethod
    def get_available_clubs():
        return CoachClub.query.filter(
            CoachClub.is_active == True,
            CoachClub.max_players > db.func.json_length(CoachClub.current_players)
        ).order_by(desc(CoachClub.rating)).all()
    
    @staticmethod
    def get_all_clubs():
        return CoachClub.query.order_by(desc(CoachClub.created_at)).all()
    
    @staticmethod
    def update_club(club_id, data):
        club = CoachClub.query.get(club_id)
        if not club:
            raise ValueError("Club non trouvé")
        
        if 'club_name' in data:
            club.club_name = data['club_name']
        if 'description' in data:
            club.description = data['description']
        if 'logo_url' in data:
            club.logo_url = data['logo_url']
        if 'budget' in data:
            club.budget = data['budget']
        if 'subscription_fee' in data:
            club.subscription_fee = data['subscription_fee']
        if 'max_players' in data:
            club.max_players = data['max_players']
        if 'specialties' in data:
            club.specialties = data['specialties']
        if 'is_active' in data:
            club.is_active = data['is_active']
        
        club.updated_at = datetime.utcnow()
        db.session.commit()
        return club
    
    @staticmethod
    def update_budget(club_id, new_budget):
        club = CoachClub.query.get(club_id)
        if not club:
            raise ValueError("Club non trouvé")
        
        club.budget = new_budget
        club.updated_at = datetime.utcnow()
        db.session.commit()
        return club
    
    @staticmethod
    def update_subscription_fee(club_id, new_fee):
        club = CoachClub.query.get(club_id)
        if not club:
            raise ValueError("Club non trouvé")
        
        club.subscription_fee = new_fee
        club.updated_at = datetime.utcnow()
        db.session.commit()
        return club
    
    @staticmethod
    def add_player_to_club(club_id, player_id):
        club = CoachClub.query.get(club_id)
        if not club:
            raise ValueError("Club non trouvé")
        
        # Vérifier que le joueur existe et est un joueur
        player = User.query.get(player_id)
        if not player or player.role != UserRole.PLAYER:
            raise ValueError("Joueur non valide")
        
        # Vérifier si le joueur a déjà un club
        existing_club = CoachClub.query.filter(
            CoachClub.current_players.contains(player_id)
        ).first()
        if existing_club:
            raise ValueError("Ce joueur est déjà dans un club")
        
        # Vérifier la disponibilité
        current_players = club.current_players or []
        if len(current_players) >= club.max_players:
            raise ValueError("Le club est complet")
        
        # Ajouter le joueur
        current_players.append(player_id)
        club.current_players = current_players
        club.total_players = len(current_players)
        club.updated_at = datetime.utcnow()
        
        db.session.commit()
        return club
    
    @staticmethod
    def remove_player_from_club(club_id, player_id):
        club = CoachClub.query.get(club_id)
        if not club:
            raise ValueError("Club non trouvé")
        
        current_players = club.current_players or []
        if player_id in current_players:
            current_players.remove(player_id)
            club.current_players = current_players
            club.total_players = len(current_players)
            club.updated_at = datetime.utcnow()
            db.session.commit()
        
        return club
    
    @staticmethod
    def toggle_club_active(club_id):
        club = CoachClub.query.get(club_id)
        if not club:
            raise ValueError("Club non trouvé")
        
        club.is_active = not club.is_active
        club.updated_at = datetime.utcnow()
        db.session.commit()
        return club