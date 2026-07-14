from datetime import datetime
from sqlalchemy import desc, func
from models import db, TrainingSession, TrainingType, SkillLevel, User, Transaction, TransactionType, TransactionStatus
import uuid

class TrainingService:
    @staticmethod
    def create_session(player_id, training_type, score, duration, level, metrics=None, video_url=None, ai_feedback=None):
        """Crée une nouvelle session d'entraînement"""
        try:
            # Vérifier si le joueur existe
            player = User.query.get(player_id)
            if not player:
                raise ValueError("Joueur non trouvé")
            
            # Calculer la récompense
            reward = TrainingService._calculate_reward(score, training_type)
            
            # Créer la session
            session = TrainingSession(
                id=str(uuid.uuid4()),
                player_id=player_id,
                type=TrainingType(training_type) if isinstance(training_type, str) else training_type,
                score=score,
                duration=duration,
                level=SkillLevel(level) if isinstance(level, str) else level,
                reward=reward,
                video_url=video_url,
                ai_feedback=ai_feedback,
                metrics=metrics or {},
                created_at=datetime.utcnow()
            )
            
            db.session.add(session)
            
            # Ajouter la récompense au wallet du joueur
            player.wallet_balance = (player.wallet_balance or 0) + reward
            
            # Créer une transaction pour la récompense
            transaction = Transaction(
                id=str(uuid.uuid4()),
                user_id=player_id,
                amount=reward,
                type=TransactionType.REWARD,
                status=TransactionStatus.COMPLETED,
                description=f"Récompense pour entraînement {session.type.value}",
                created_at=datetime.utcnow()
            )
            db.session.add(transaction)
            
            db.session.commit()
            return session
            
        except Exception as e:
            db.session.rollback()
            raise e
    
    @staticmethod
    def _calculate_reward(score, training_type):
        """Calcule la récompense basée sur le score et le type d'entraînement"""
        base_reward = 1.0
        multiplier = score / 100
        
        # Bonus selon le type d'entraînement
        type_bonus = {
            TrainingType.SPEED: 1.2,
            TrainingType.CONTROL_BALL: 1.0,
            TrainingType.SHOOT: 1.1,
            TrainingType.PASS: 0.9
        }
        
        bonus = type_bonus.get(training_type, 1.0)
        reward = base_reward * multiplier * 10 * bonus
        
        # Limiter entre 0.5 et 10 DT
        return min(max(reward, 0.5), 10.0)
    
    @staticmethod
    def get_player_sessions(player_id, training_type=None):
        """Récupère les sessions d'entraînement d'un joueur"""
        query = TrainingSession.query.filter_by(player_id=player_id)
        if training_type:
            query = query.filter_by(type=TrainingType(training_type))
        return query.order_by(desc(TrainingSession.created_at)).all()
    
    @staticmethod
    def get_last_session(player_id, training_type):
        """Récupère la dernière session d'entraînement d'un type spécifique"""
        session = TrainingSession.query.filter_by(
            player_id=player_id,
            type=TrainingType(training_type)
        ).order_by(desc(TrainingSession.created_at)).first()
        return session
    
    @staticmethod
    def get_average_score(player_id, training_type):
        """Récupère le score moyen pour un type d'entraînement"""
        result = db.session.query(func.avg(TrainingSession.score)).filter(
            TrainingSession.player_id == player_id,
            TrainingSession.type == TrainingType(training_type)
        ).scalar()
        return result or 0.0
    
    @staticmethod
    def get_total_rewards(player_id):
        """Récupère le total des récompenses d'un joueur"""
        result = db.session.query(func.sum(TrainingSession.reward)).filter(
            TrainingSession.player_id == player_id
        ).scalar()
        return result or 0.0
    
    @staticmethod
    def get_player_stats_summary(player_id):
        """Récupère un résumé des statistiques d'entraînement"""
        sessions = TrainingSession.query.filter_by(player_id=player_id).all()
        
        if not sessions:
            return {
                'total_sessions': 0,
                'average_score': 0.0,
                'best_score': 0.0,
                'total_rewards': 0.0,
                'last_training': None
            }
        
        return {
            'total_sessions': len(sessions),
            'average_score': sum(s.score for s in sessions) / len(sessions),
            'best_score': max(s.score for s in sessions),
            'total_rewards': sum(s.reward for s in sessions),
            'last_training': max(sessions, key=lambda s: s.created_at).to_dict() if sessions else None
        }
    
    @staticmethod
    def get_club_sessions(club_id):
        """Récupère toutes les sessions d'entraînement d'un club"""
        from models import CoachClub
        club = CoachClub.query.get(club_id)
        if not club:
            raise ValueError("Club non trouvé")
        
        players = club.current_players or []
        if not players:
            return []
        
        return TrainingSession.query.filter(
            TrainingSession.player_id.in_(players)
        ).order_by(desc(TrainingSession.created_at)).all()
    
    @staticmethod
    def get_training_statistics_by_type(player_id):
        """Récupère les statistiques par type d'entraînement"""
        stats = {}
        for type_enum in TrainingType:
            sessions = TrainingSession.query.filter_by(
                player_id=player_id,
                type=type_enum
            ).all()
            
            if sessions:
                stats[type_enum.value] = {
                    'count': len(sessions),
                    'average_score': sum(s.score for s in sessions) / len(sessions),
                    'best_score': max(s.score for s in sessions),
                    'total_rewards': sum(s.reward for s in sessions),
                    'last_session': max(sessions, key=lambda s: s.created_at).to_dict() if sessions else None
                }
            else:
                stats[type_enum.value] = {
                    'count': 0,
                    'average_score': 0.0,
                    'best_score': 0.0,
                    'total_rewards': 0.0,
                    'last_session': None
                }
        
        return stats
    
    @staticmethod
    def get_leaderboard(limit=10, club_id=None):
        """Récupère le classement des joueurs"""
        query = db.session.query(
            User.id,
            User.full_name,
            func.avg(TrainingSession.score).label('avg_score'),
            func.sum(TrainingSession.reward).label('total_rewards'),
            func.count(TrainingSession.id).label('session_count'),
            func.max(TrainingSession.score).label('best_score')
        ).join(TrainingSession, User.id == TrainingSession.player_id)
        
        if club_id:
            from models import CoachClub
            club = CoachClub.query.get(club_id)
            if club and club.current_players:
                query = query.filter(User.id.in_(club.current_players))
        
        results = query.group_by(User.id).order_by(desc('avg_score')).limit(limit).all()
        
        leaderboard = []
        for rank, result in enumerate(results, 1):
            leaderboard.append({
                'rank': rank,
                'player_id': result.id,
                'player_name': result.full_name,
                'avg_score': float(result.avg_score) if result.avg_score else 0.0,
                'total_rewards': float(result.total_rewards) if result.total_rewards else 0.0,
                'session_count': result.session_count,
                'best_score': float(result.best_score) if result.best_score else 0.0
            })
        
        return leaderboard
    
    @staticmethod
    def get_session_by_id(session_id):
        """Récupère une session par son ID"""
        return TrainingSession.query.get(session_id)
    
    @staticmethod
    def delete_session(session_id, user_id):
        """Supprime une session d'entraînement"""
        session = TrainingSession.query.get(session_id)
        if not session:
            raise ValueError("Session non trouvée")
        
        # Vérifier que l'utilisateur est le propriétaire
        if session.player_id != user_id:
            raise ValueError("Accès non autorisé")
        
        # Supprimer la récompense du wallet
        player = User.query.get(user_id)
        if player:
            player.wallet_balance -= session.reward
        
        db.session.delete(session)
        db.session.commit()
        return True
    
    @staticmethod
    def get_player_progress(player_id):
        """Récupère la progression du joueur sur toutes les compétences"""
        sessions = TrainingSession.query.filter_by(player_id=player_id).all()
        
        if not sessions:
            return {
                'overall_progress': 0.0,
                'skills_progress': {},
                'total_sessions': 0,
                'total_rewards': 0.0
            }
        
        # Calculer la progression par type
        skills_progress = {}
        for type_enum in TrainingType:
            type_sessions = [s for s in sessions if s.type == type_enum]
            if type_sessions:
                # Trier par date
                sorted_sessions = sorted(type_sessions, key=lambda s: s.created_at)
                first_score = sorted_sessions[0].score
                last_score = sorted_sessions[-1].score
                progress = ((last_score - first_score) / (first_score + 0.01)) * 100
                skills_progress[type_enum.value] = max(0, min(100, progress))
            else:
                skills_progress[type_enum.value] = 0.0
        
        # Calculer la progression globale
        avg_first = sum(sessions[0].score for sessions in [sessions]) / len(sessions)
        avg_last = sum(sessions[-1].score for sessions in [sessions]) / len(sessions)
        overall_progress = ((avg_last - avg_first) / (avg_first + 0.01)) * 100
        
        return {
            'overall_progress': max(0, min(100, overall_progress)),
            'skills_progress': skills_progress,
            'total_sessions': len(sessions),
            'total_rewards': sum(s.reward for s in sessions)
        }