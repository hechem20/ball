from datetime import datetime, timedelta
from sqlalchemy import func, desc, and_
from models import (
    db,
    User,
    UserRole,
    TrainingSession,
    TrainingType,
    SkillLevel,
    CoachClub,
    Transaction,
    TransactionType
)
import json

class PlayerStatsService:
    """Service pour gérer les statistiques des joueurs"""
    
    @staticmethod
    def get_player_stats(player_id):
        """
        Récupère les statistiques complètes d'un joueur
        
        Args:
            player_id (str): ID du joueur
            
        Returns:
            dict: Statistiques complètes du joueur
        """
        try:
            player = User.query.get(player_id)
            if not player:
                raise ValueError("Joueur non trouvé")
            
            # Récupérer toutes les sessions d'entraînement
            trainings = TrainingSession.query.filter_by(player_id=player_id).all()
            
            if not trainings:
                return PlayerStatsService._get_empty_stats(player)
            
            # Calculer les statistiques par type
            speed_trainings = [t for t in trainings if t.type == TrainingType.SPEED]
            control_trainings = [t for t in trainings if t.type == TrainingType.CONTROL_BALL]
            shoot_trainings = [t for t in trainings if t.type == TrainingType.SHOOT]
            pass_trainings = [t for t in trainings if t.type == TrainingType.PASS]
            
            # Scores moyens par type
            speed_score = sum(t.score for t in speed_trainings) / len(speed_trainings) if speed_trainings else 0.0
            control_score = sum(t.score for t in control_trainings) / len(control_trainings) if control_trainings else 0.0
            shoot_score = sum(t.score for t in shoot_trainings) / len(shoot_trainings) if shoot_trainings else 0.0
            pass_score = sum(t.score for t in pass_trainings) / len(pass_trainings) if pass_trainings else 0.0
            
            # Score total
            total_score = speed_score + control_score + shoot_score + pass_score
            
            # Récompenses totales
            total_rewards = sum(t.reward for t in trainings)
            
            # Meilleurs scores par type
            best_scores = {}
            for type_enum in TrainingType:
                type_trainings = [t for t in trainings if t.type == type_enum]
                if type_trainings:
                    best_scores[type_enum.value] = max(t.score for t in type_trainings)
                else:
                    best_scores[type_enum.value] = 0.0
            
            # Nombre de sessions par type
            sessions_count = {}
            for type_enum in TrainingType:
                sessions_count[type_enum.value] = len([t for t in trainings if t.type == type_enum])
            
            # Niveau global
            avg_score = total_score / 4 if total_score > 0 else 0.0
            overall_level = PlayerStatsService._get_skill_level(avg_score)
            
            # Taux de progression
            progress_rate = PlayerStatsService._calculate_progress(trainings)
            
            # Dernières sessions
            last_sessions = sorted(trainings, key=lambda t: t.created_at, reverse=True)[:5]
            
            # Statistiques par semaine
            weekly_stats = PlayerStatsService._get_weekly_stats(trainings)
            
            return {
                'player_id': player.id,
                'player_name': player.full_name,
                'email': player.email,
                'phone': player.phone or '',
                'joined_date': player.created_at.isoformat() if player.created_at else None,
                'speed_score': round(speed_score, 2),
                'control_ball_score': round(control_score, 2),
                'shoot_score': round(shoot_score, 2),
                'pass_score': round(pass_score, 2),
                'total_score': round(total_score, 2),
                'total_rewards': round(total_rewards, 2),
                'training_sessions_count': len(trainings),
                'best_scores': best_scores,
                'sessions_count': sessions_count,
                'overall_level': overall_level.value,
                'progress_rate': round(progress_rate, 2),
                'last_sessions': [t.to_dict() for t in last_sessions],
                'weekly_stats': weekly_stats,
                'wallet_balance': player.wallet_balance,
                'club': PlayerStatsService._get_player_club(player_id)
            }
            
        except Exception as e:
            print(f"❌ Erreur get_player_stats: {e}")
            raise

    @staticmethod
    def _get_empty_stats(player):
        """Retourne des statistiques vides pour un joueur sans entraînement"""
        return {
            'player_id': player.id,
            'player_name': player.full_name,
            'email': player.email,
            'phone': player.phone or '',
            'joined_date': player.created_at.isoformat() if player.created_at else None,
            'speed_score': 0.0,
            'control_ball_score': 0.0,
            'shoot_score': 0.0,
            'pass_score': 0.0,
            'total_score': 0.0,
            'total_rewards': 0.0,
            'training_sessions_count': 0,
            'best_scores': {t.value: 0.0 for t in TrainingType},
            'sessions_count': {t.value: 0 for t in TrainingType},
            'overall_level': SkillLevel.BEGINNER.value,
            'progress_rate': 0.0,
            'last_sessions': [],
            'weekly_stats': [],
            'wallet_balance': player.wallet_balance,
            'club': PlayerStatsService._get_player_club(player.id)
        }

    @staticmethod
    def _get_skill_level(avg_score):
        """Détermine le niveau de compétence basé sur le score moyen"""
        if avg_score >= 90:
            return SkillLevel.EXPERT
        elif avg_score >= 75:
            return SkillLevel.ADVANCED
        elif avg_score >= 50:
            return SkillLevel.INTERMEDIATE
        else:
            return SkillLevel.BEGINNER

    @staticmethod
    def _calculate_progress(trainings):
        """Calcule le taux de progression du joueur"""
        if len(trainings) < 2:
            return 0.0
        
        sorted_trainings = sorted(trainings, key=lambda t: t.created_at)
        
        # Grouper par type et prendre les 5 premiers et 5 derniers
        progress_by_type = {}
        for type_enum in TrainingType:
            type_trainings = [t for t in sorted_trainings if t.type == type_enum]
            if len(type_trainings) >= 3:
                # Prendre la moyenne des 3 premiers et des 3 derniers
                first_avg = sum(t.score for t in type_trainings[:3]) / min(3, len(type_trainings[:3]))
                last_avg = sum(t.score for t in type_trainings[-3:]) / min(3, len(type_trainings[-3:]))
                
                if first_avg > 0:
                    progress_by_type[type_enum.value] = ((last_avg - first_avg) / first_avg) * 100
                else:
                    progress_by_type[type_enum.value] = 0.0
        
        # Moyenne des progressions
        if progress_by_type:
            avg_progress = sum(progress_by_type.values()) / len(progress_by_type)
            return max(0, min(100, avg_progress))
        
        # Si pas assez de données, utiliser la différence entre la première et la dernière session
        if len(sorted_trainings) >= 3:
            first_avg = sum(t.score for t in sorted_trainings[:3]) / 3
            last_avg = sum(t.score for t in sorted_trainings[-3:]) / 3
            if first_avg > 0:
                progress = ((last_avg - first_avg) / first_avg) * 100
                return max(0, min(100, progress))
        
        return 0.0

    @staticmethod
    def _get_weekly_stats(trainings):
        """Récupère les statistiques par semaine"""
        weekly_stats = []
        
        # Grouper par semaine
        for i in range(4):
            week_start = datetime.utcnow() - timedelta(days=(i * 7) + 7)
            week_end = datetime.utcnow() - timedelta(days=i * 7)
            
            week_trainings = [
                t for t in trainings 
                if week_start <= t.created_at <= week_end
            ]
            
            if week_trainings:
                avg_score = sum(t.score for t in week_trainings) / len(week_trainings)
                total_rewards = sum(t.reward for t in week_trainings)
            else:
                avg_score = 0.0
                total_rewards = 0.0
            
            weekly_stats.append({
                'week': f'Semaine {4 - i}',
                'start_date': week_start.isoformat(),
                'end_date': week_end.isoformat(),
                'avg_score': round(avg_score, 2),
                'total_rewards': round(total_rewards, 2),
                'sessions_count': len(week_trainings)
            })
        
        return weekly_stats

    @staticmethod
    def _get_player_club(player_id):
        """Récupère le club du joueur"""
        try:
            club = CoachClub.query.filter(
                CoachClub.current_players.contains(player_id)
            ).first()
            
            if club:
                return {
                    'club_id': club.id,
                    'club_name': club.club_name,
                    'coach_id': club.coach_id,
                    'coach_name': club.coach.full_name if club.coach else None,
                    'joined_date': club.created_at.isoformat() if club.created_at else None
                }
            return None
        except Exception as e:
            print(f"❌ Erreur _get_player_club: {e}")
            return None

    @staticmethod
    def get_club_players_stats(club_id):
        """
        Récupère les statistiques de tous les joueurs d'un club
        
        Args:
            club_id (str): ID du club
            
        Returns:
            list: Liste des statistiques des joueurs
        """
        try:
            club = CoachClub.query.get(club_id)
            if not club:
                raise ValueError("Club non trouvé")
            
            players_stats = []
            for player_id in club.current_players or []:
                try:
                    stats = PlayerStatsService.get_player_stats(player_id)
                    players_stats.append(stats)
                except Exception as e:
                    print(f"Erreur chargement stats joueur {player_id}: {e}")
                    # Ajouter des stats par défaut
                    player = User.query.get(player_id)
                    if player:
                        players_stats.append(PlayerStatsService._get_empty_stats(player))
            
            # Trier par score total décroissant
            players_stats.sort(key=lambda p: p['total_score'], reverse=True)
            
            return players_stats
            
        except Exception as e:
            print(f"❌ Erreur get_club_players_stats: {e}")
            raise

    @staticmethod
    def get_player_progress(player_id, days=30):
        """
        Récupère la progression du joueur sur une période donnée
        
        Args:
            player_id (str): ID du joueur
            days (int): Nombre de jours
            
        Returns:
            dict: Données de progression
        """
        try:
            start_date = datetime.utcnow() - timedelta(days=days)
            
            trainings = TrainingSession.query.filter(
                and_(
                    TrainingSession.player_id == player_id,
                    TrainingSession.created_at >= start_date
                )
            ).order_by(TrainingSession.created_at).all()
            
            if not trainings:
                return {
                    'progress_data': [],
                    'average_score': 0.0,
                    'total_sessions': 0,
                    'improvement': 0.0
                }
            
            # Grouper par jour
            daily_data = {}
            for training in trainings:
                date_key = training.created_at.date().isoformat()
                if date_key not in daily_data:
                    daily_data[date_key] = {
                        'date': date_key,
                        'scores': [],
                        'total_rewards': 0.0,
                        'sessions_count': 0
                    }
                daily_data[date_key]['scores'].append(training.score)
                daily_data[date_key]['total_rewards'] += training.reward
                daily_data[date_key]['sessions_count'] += 1
            
            # Calculer les moyennes quotidiennes
            progress_data = []
            for date_key, data in sorted(daily_data.items()):
                progress_data.append({
                    'date': date_key,
                    'avg_score': round(sum(data['scores']) / len(data['scores']), 2),
                    'total_rewards': round(data['total_rewards'], 2),
                    'sessions_count': data['sessions_count']
                })
            
            # Calculer l'amélioration
            if len(progress_data) >= 2:
                first_avg = progress_data[0]['avg_score']
                last_avg = progress_data[-1]['avg_score']
                improvement = ((last_avg - first_avg) / (first_avg + 0.01)) * 100
            else:
                improvement = 0.0
            
            return {
                'progress_data': progress_data,
                'average_score': round(sum(t.score for t in trainings) / len(trainings), 2),
                'total_sessions': len(trainings),
                'total_rewards': round(sum(t.reward for t in trainings), 2),
                'improvement': round(max(0, improvement), 2)
            }
            
        except Exception as e:
            print(f"❌ Erreur get_player_progress: {e}")
            raise

    @staticmethod
    def get_player_achievements(player_id):
        """
        Récupère les accomplissements du joueur
        
        Args:
            player_id (str): ID du joueur
            
        Returns:
            list: Liste des accomplissements
        """
        try:
            trainings = TrainingSession.query.filter_by(player_id=player_id).all()
            achievements = []
            
            # Vérifier différents accomplissements
            total_trainings = len(trainings)
            if total_trainings >= 10:
                achievements.append({
                    'title': '🏅 Débutant Déterminé',
                    'description': '10 sessions d\'entraînement complétées',
                    'icon': 'emoji_events',
                    'earned_at': datetime.utcnow().isoformat()
                })
            
            if total_trainings >= 50:
                achievements.append({
                    'title': '🥈 Athlète Dévoué',
                    'description': '50 sessions d\'entraînement complétées',
                    'icon': 'emoji_events',
                    'earned_at': datetime.utcnow().isoformat()
                })
            
            if total_trainings >= 100:
                achievements.append({
                    'title': '🥇 Champion Persévérant',
                    'description': '100 sessions d\'entraînement complétées',
                    'icon': 'emoji_events',
                    'earned_at': datetime.utcnow().isoformat()
                })
            
            # Scores parfaits
            perfect_sessions = [t for t in trainings if t.score >= 95]
            if perfect_sessions:
                achievements.append({
                    'title': '🎯 Maître de la Précision',
                    'description': f'{len(perfect_sessions)} sessions avec un score ≥ 95%',
                    'icon': 'target',
                    'earned_at': max(perfect_sessions, key=lambda t: t.created_at).created_at.isoformat()
                })
            
            # Récompenses totales
            total_rewards = sum(t.reward for t in trainings)
            if total_rewards >= 100:
                achievements.append({
                    'title': '💰 Économiseur Expert',
                    'description': f'{total_rewards:.2f} DT de récompenses accumulées',
                    'icon': 'savings',
                    'earned_at': datetime.utcnow().isoformat()
                })
            
            # Meilleur score par type
            for type_enum in TrainingType:
                type_trainings = [t for t in trainings if t.type == type_enum]
                if type_trainings and max(t.score for t in type_trainings) >= 90:
                    achievements.append({
                        'title': f'⭐ Expert en {type_enum.value.capitalize()}',
                        'description': f'Score {type_enum.value} ≥ 90%',
                        'icon': 'star',
                        'earned_at': max(type_trainings, key=lambda t: t.score).created_at.isoformat()
                    })
            
            # Limiter à 10 accomplissements
            return achievements[:10]
            
        except Exception as e:
            print(f"❌ Erreur get_player_achievements: {e}")
            return []

    @staticmethod
    def get_top_performers(club_id=None, limit=10):
        """
        Récupère les meilleurs performeurs
        
        Args:
            club_id (str, optional): ID du club
            limit (int): Nombre de résultats
            
        Returns:
            list: Liste des meilleurs performeurs
        """
        try:
            query = db.session.query(
                User.id,
                User.full_name,
                func.avg(TrainingSession.score).label('avg_score'),
                func.sum(TrainingSession.reward).label('total_rewards'),
                func.count(TrainingSession.id).label('session_count')
            ).join(TrainingSession, User.id == TrainingSession.player_id)
            
            if club_id:
                club = CoachClub.query.get(club_id)
                if club and club.current_players:
                    query = query.filter(User.id.in_(club.current_players))
            
            results = query.group_by(User.id).order_by(desc('avg_score')).limit(limit).all()
            
            top_performers = []
            for rank, result in enumerate(results, 1):
                top_performers.append({
                    'rank': rank,
                    'player_id': result.id,
                    'player_name': result.full_name,
                    'avg_score': round(float(result.avg_score), 2) if result.avg_score else 0.0,
                    'total_rewards': round(float(result.total_rewards), 2) if result.total_rewards else 0.0,
                    'session_count': result.session_count or 0
                })
            
            return top_performers
            
        except Exception as e:
            print(f"❌ Erreur get_top_performers: {e}")
            return []

    @staticmethod
    def get_player_ranking(player_id, club_id=None):
        """
        Récupère le classement d'un joueur
        
        Args:
            player_id (str): ID du joueur
            club_id (str, optional): ID du club
            
        Returns:
            dict: Classement du joueur
        """
        try:
            # Récupérer le score moyen du joueur
            trainings = TrainingSession.query.filter_by(player_id=player_id).all()
            if not trainings:
                return {'rank': 0, 'total_players': 0, 'avg_score': 0.0}
            
            player_avg = sum(t.score for t in trainings) / len(trainings)
            
            # Récupérer tous les joueurs du club
            if club_id:
                club = CoachClub.query.get(club_id)
                if club and club.current_players:
                    player_ids = club.current_players
                else:
                    player_ids = []
            else:
                # Tous les joueurs
                player_ids = [u.id for u in User.query.filter_by(role=UserRole.PLAYER).all()]
            
            # Calculer les scores moyens de tous les joueurs
            all_players_stats = []
            for pid in player_ids:
                p_trainings = TrainingSession.query.filter_by(player_id=pid).all()
                if p_trainings:
                    avg = sum(t.score for t in p_trainings) / len(p_trainings)
                    all_players_stats.append({'player_id': pid, 'avg_score': avg})
            
            # Trier par score décroissant
            all_players_stats.sort(key=lambda x: x['avg_score'], reverse=True)
            
            # Trouver le rang du joueur
            rank = 1
            for i, stat in enumerate(all_players_stats, 1):
                if stat['player_id'] == player_id:
                    rank = i
                    break
            
            return {
                'rank': rank,
                'total_players': len(all_players_stats),
                'avg_score': round(player_avg, 2),
                'percentile': round((1 - rank / len(all_players_stats)) * 100, 2) if all_players_stats else 0.0
            }
            
        except Exception as e:
            print(f"❌ Erreur get_player_ranking: {e}")
            return {'rank': 0, 'total_players': 0, 'avg_score': 0.0}

    @staticmethod
    def get_training_recommendations(player_id):
        """
        Génère des recommandations d'entraînement personnalisées
        
        Args:
            player_id (str): ID du joueur
            
        Returns:
            list: Liste des recommandations
        """
        try:
            stats = PlayerStatsService.get_player_stats(player_id)
            
            recommendations = []
            
            # Identifier les points faibles
            if stats['speed_score'] < 50:
                recommendations.append({
                    'type': 'speed',
                    'title': 'Améliorez votre vitesse',
                    'description': 'Exercices de sprint et d\'accélération pour augmenter votre vitesse',
                    'difficulty': 'intermediate',
                    'expected_improvement': '15-20%'
                })
            elif stats['speed_score'] < 75:
                recommendations.append({
                    'type': 'speed',
                    'title': 'Optimisez votre vitesse',
                    'description': 'Travaillez votre technique de course et votre explosivité',
                    'difficulty': 'advanced',
                    'expected_improvement': '10-15%'
                })
            
            if stats['control_ball_score'] < 50:
                recommendations.append({
                    'type': 'control_ball',
                    'title': 'Maîtrisez le contrôle de balle',
                    'description': 'Exercices de dribble et de contrôle pour améliorer votre technique',
                    'difficulty': 'intermediate',
                    'expected_improvement': '15-20%'
                })
            elif stats['control_ball_score'] < 75:
                recommendations.append({
                    'type': 'control_ball',
                    'title': 'Perfectionnez votre contrôle',
                    'description': 'Exercices avancés de dribble et de première touche',
                    'difficulty': 'advanced',
                    'expected_improvement': '10-15%'
                })
            
            if stats['shoot_score'] < 50:
                recommendations.append({
                    'type': 'shoot',
                    'title': 'Améliorez votre tir',
                    'description': 'Exercices de précision et de puissance de tir',
                    'difficulty': 'intermediate',
                    'expected_improvement': '15-20%'
                })
            elif stats['shoot_score'] < 75:
                recommendations.append({
                    'type': 'shoot',
                    'title': 'Optimisez votre précision',
                    'description': 'Travaillez votre placement et votre technique de frappe',
                    'difficulty': 'advanced',
                    'expected_improvement': '10-15%'
                })
            
            if stats['pass_score'] < 50:
                recommendations.append({
                    'type': 'pass',
                    'title': 'Maîtrisez les passes',
                    'description': 'Exercices de précision et de vision de jeu',
                    'difficulty': 'intermediate',
                    'expected_improvement': '15-20%'
                })
            elif stats['pass_score'] < 75:
                recommendations.append({
                    'type': 'pass',
                    'title': 'Perfectionnez vos passes',
                    'description': 'Exercices avancés de passes courtes et longues',
                    'difficulty': 'advanced',
                    'expected_improvement': '10-15%'
                })
            
            # Recommandation générale si tout va bien
            if not recommendations:
                recommendations.append({
                    'type': 'general',
                    'title': 'Maintenez votre niveau',
                    'description': 'Continue à t\'entraîner régulièrement pour maintenir et améliorer tes performances',
                    'difficulty': 'maintenance',
                    'expected_improvement': '5-10%'
                })
            
            return recommendations[:5]  # Limiter à 5 recommandations
            
        except Exception as e:
            print(f"❌ Erreur get_training_recommendations: {e}")
            return []

    @staticmethod
    def get_training_statistics_by_type(player_id):
        """
        Récupère les statistiques par type d'entraînement
        
        Args:
            player_id (str): ID du joueur
            
        Returns:
            dict: Statistiques par type
        """
        try:
            stats = {}
            for type_enum in TrainingType:
                sessions = TrainingSession.query.filter_by(
                    player_id=player_id,
                    type=type_enum
                ).all()
                
                if sessions:
                    stats[type_enum.value] = {
                        'count': len(sessions),
                        'average_score': round(sum(s.score for s in sessions) / len(sessions), 2),
                        'best_score': round(max(s.score for s in sessions), 2),
                        'worst_score': round(min(s.score for s in sessions), 2),
                        'total_rewards': round(sum(s.reward for s in sessions), 2),
                        'last_session': max(sessions, key=lambda s: s.created_at).to_dict() if sessions else None
                    }
                else:
                    stats[type_enum.value] = {
                        'count': 0,
                        'average_score': 0.0,
                        'best_score': 0.0,
                        'worst_score': 0.0,
                        'total_rewards': 0.0,
                        'last_session': None
                    }
            
            return stats
            
        except Exception as e:
            print(f"❌ Erreur get_training_statistics_by_type: {e}")
            return {}

    @staticmethod
    def get_player_summary(player_id):
        """
        Récupère un résumé des statistiques du joueur
        
        Args:
            player_id (str): ID du joueur
            
        Returns:
            dict: Résumé des statistiques
        """
        try:
            stats = PlayerStatsService.get_player_stats(player_id)
            
            return {
                'player_id': player_id,
                'player_name': stats['player_name'],
                'total_score': stats['total_score'],
                'overall_level': stats['overall_level'],
                'progress_rate': stats['progress_rate'],
                'total_rewards': stats['total_rewards'],
                'training_sessions': stats['training_sessions_count'],
                'best_skill': PlayerStatsService._get_best_skill(stats),
                'worst_skill': PlayerStatsService._get_worst_skill(stats),
                'club': stats['club']
            }
            
        except Exception as e:
            print(f"❌ Erreur get_player_summary: {e}")
            return {}

    @staticmethod
    def _get_best_skill(stats):
        """Trouve la meilleure compétence du joueur"""
        skills = {
            'speed': stats['speed_score'],
            'control_ball': stats['control_ball_score'],
            'shoot': stats['shoot_score'],
            'pass': stats['pass_score']
        }
        best = max(skills, key=skills.get)
        return {
            'skill': best,
            'score': stats[f'{best}_score']
        }

    @staticmethod
    def _get_worst_skill(stats):
        """Trouve la pire compétence du joueur"""
        skills = {
            'speed': stats['speed_score'],
            'control_ball': stats['control_ball_score'],
            'shoot': stats['shoot_score'],
            'pass': stats['pass_score']
        }
        worst = min(skills, key=skills.get)
        return {
            'skill': worst,
            'score': stats[f'{worst}_score']
        }
