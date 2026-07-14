from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, create_refresh_token, jwt_required, get_jwt_identity
from models import db, User, UserRole, CoachClub, TrainingSession, TrainingType, SkillLevel, Transaction, TransactionType, TransactionStatus
from services.auth_service import AuthService
from services.club_service import ClubService
from services.player_stats_service import PlayerStatsService
from services.training_service import TrainingService
from services.analysis_service import AIService
from datetime import datetime
import uuid
import os
import tempfile
from werkzeug.utils import secure_filename
from services.wallet_service import WalletService

# ==================== BLUEPRINTS ====================

auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')
club_bp = Blueprint('club', __name__, url_prefix='/api/clubs')
training_bp = Blueprint('training', __name__, url_prefix='/api/training')
payment_bp = Blueprint('payment', __name__, url_prefix='/api/payments')
stats_bp = Blueprint('stats', __name__, url_prefix='/api/stats')

# ==================== ROUTES AUTHENTIFICATION ====================
wallet_bp = Blueprint("wallet", __name__, url_prefix="/api/wallet")

@wallet_bp.route("/balance", methods=["GET"])
@jwt_required()
def balance():

    user_id = get_jwt_identity()

    balance = WalletService.get_balance(user_id)

    return jsonify({
        "balance": balance
    })
@auth_bp.route('/register', methods=['POST'])
def register():
    """Inscription d'un nouvel utilisateur"""
    try:
        data = request.get_json()
        
        required_fields = ['full_name', 'email', 'password', 'phone', 'role']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Champ {field} requis'}), 400
        
        existing_user = User.query.filter_by(email=data['email']).first()
        if existing_user:
            return jsonify({'error': 'Cet email est déjà utilisé'}), 400
        
        if data['role'] not in ['player', 'coach']:
            return jsonify({'error': 'Rôle invalide'}), 400
        
        user = User(
            id=str(uuid.uuid4()),
            full_name=data['full_name'],
            email=data['email'],
            password_hash=AuthService.hash_password(data['password']),
            phone=data['phone'],
            role=UserRole(data['role']),
            experience=data.get('experience'),
            wallet_balance=100.0
        )
        
        db.session.add(user)
        db.session.commit()
        
        if user.role == UserRole.COACH:
            club_data = {
                'coach_id': user.id,
                'club_name': data.get('club_name', f"Club de {user.full_name}"),
                'description': data.get('club_description', 'Club de football professionnel'),
                'budget': data.get('budget', 10000.0),
                'subscription_fee': data.get('subscription_fee', 50.0),
                'max_players': data.get('max_players', 30),
                'specialties': data.get('specialties', ['Football', 'Tactique', 'Technique'])
            }
            ClubService.create_club(club_data)
        
        access_token = create_access_token(identity=user.id)
        refresh_token = create_refresh_token(identity=user.id)
        
        return jsonify({
            'success': True,
            'message': 'Inscription réussie',
            'user': user.to_dict(),
            'access_token': access_token,
            'refresh_token': refresh_token
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@auth_bp.route('/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        
        if not data.get('email') or not data.get('password'):
            return jsonify({'error': 'Email et mot de passe requis'}), 400
        
        user = User.query.filter_by(email=data['email']).first()
        
        if not user or not AuthService.verify_password(data['password'], user.password_hash):
            return jsonify({'error': 'Email ou mot de passe incorrect'}), 401
        
        if not user.is_active:
            return jsonify({'error': 'Compte désactivé'}), 403
        
        access_token = create_access_token(identity=user.id)
        refresh_token = create_refresh_token(identity=user.id)
        
        return jsonify({
            'success': True,
            'message': 'Connexion réussie',
            'user': user.to_dict(),
            'access_token': access_token,
            'refresh_token': refresh_token
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@auth_bp.route('/me', methods=['GET'])
@jwt_required()
def get_current_user():
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': 'Utilisateur non trouvé'}), 404
        return jsonify(user.to_dict()), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@auth_bp.route('/wallet', methods=['GET'])
@jwt_required()
def get_wallet():
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': 'Utilisateur non trouvé'}), 404
        return jsonify({'balance': user.wallet_balance, 'currency': 'DT'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ==================== ROUTES CLUBS ====================

@club_bp.route('/available', methods=['GET'])
def get_available_clubs():
    try:
        clubs = CoachClub.query.filter(
            CoachClub.is_active == True
        ).all()

        return jsonify({
            "clubs": [club.to_dict() for club in clubs]
        }), 200

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

@club_bp.route('/my-club', methods=['GET'])
@jwt_required()
def get_my_club():
    try:
        user_id = get_jwt_identity()
        club = CoachClub.query.filter_by(coach_id=user_id).first()
        if not club:
            return jsonify({'error': 'Aucun club trouvé'}), 404
        return jsonify(club.to_dict()), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@club_bp.route('/<club_id>', methods=['GET'])
@jwt_required()
def get_club(club_id):
    try:
        club = CoachClub.query.get(club_id)
        if not club:
            return jsonify({'error': 'Club non trouvé'}), 404
        return jsonify(club.to_dict()), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@club_bp.route('/<club_id>/budget', methods=['PUT'])
@jwt_required()
def update_budget(club_id):
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        if 'budget' not in data:
            return jsonify({'error': 'Budget requis'}), 400
        
        club = CoachClub.query.get(club_id)
        if not club:
            return jsonify({'error': 'Club non trouvé'}), 404
        
        user = User.query.get(user_id)
        if club.coach_id != user_id and user.role != UserRole.ADMIN:
            return jsonify({'error': 'Accès non autorisé'}), 403
        
        club.budget = data['budget']
        club.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({'message': 'Budget mis à jour', 'budget': club.budget}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@club_bp.route('/<club_id>/subscription-fee', methods=['PUT'])
@jwt_required()
def update_subscription_fee(club_id):
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        if 'subscription_fee' not in data:
            return jsonify({'error': 'Frais requis'}), 400
        
        club = CoachClub.query.get(club_id)
        if not club:
            return jsonify({'error': 'Club non trouvé'}), 404
        
        user = User.query.get(user_id)
        if club.coach_id != user_id and user.role != UserRole.ADMIN:
            return jsonify({'error': 'Accès non autorisé'}), 403
        
        club.subscription_fee = data['subscription_fee']
        club.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({'message': 'Frais mis à jour', 'subscription_fee': club.subscription_fee}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500



@club_bp.route('/<club_id>/add-player/<player_id>', methods=['POST'])
@jwt_required()
def add_player_to_club(club_id, player_id):
    try:
        user_id = get_jwt_identity()
        club = CoachClub.query.get(club_id)
        if not club:
            return jsonify({'error': 'Club non trouvé'}), 404
        
        user = User.query.get(user_id)
        if club.coach_id != user_id and player_id != user_id:
            return jsonify({'error': 'Accès non autorisé'}), 403
        
        player = User.query.get(player_id)
        if not player or player.role != UserRole.PLAYER:
            return jsonify({'error': 'Joueur invalide'}), 400
        
        existing_club = CoachClub.query.filter(
            CoachClub.current_players.contains(player_id)
        ).first()
        if existing_club:
            return jsonify({'error': 'Joueur déjà dans un club'}), 400
        
        current_players = club.current_players or []
        if len(current_players) >= club.max_players:
            return jsonify({'error': 'Club complet'}), 400
        
        current_players.append(player_id)
        club.current_players = current_players
        club.total_players = len(current_players)
        club.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({'message': 'Joueur ajouté', 'club': club.to_dict()}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@club_bp.route('/<club_id>/remove-player/<player_id>', methods=['DELETE'])
@jwt_required()
def remove_player_from_club(club_id, player_id):
    try:
        user_id = get_jwt_identity()
        club = CoachClub.query.get(club_id)
        if not club:
            return jsonify({'error': 'Club non trouvé'}), 404
        
        user = User.query.get(user_id)
        if club.coach_id != user_id and player_id != user_id and user.role != UserRole.ADMIN:
            return jsonify({'error': 'Accès non autorisé'}), 403
        
        current_players = club.current_players or []
        if player_id in current_players:
            current_players.remove(player_id)
            club.current_players = current_players
            club.total_players = len(current_players)
            club.updated_at = datetime.utcnow()
            db.session.commit()
            return jsonify({'message': 'Joueur retiré'}), 200
        
        return jsonify({'error': 'Joueur non trouvé'}), 404
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@club_bp.route('/<club_id>/leaderboard', methods=['GET'])
@jwt_required()
def get_leaderboard(club_id):
    try:
        club = CoachClub.query.get(club_id)
        if not club:
            return jsonify({'error': 'Club non trouvé'}), 404
        
        players = club.current_players or []
        leaderboard = []
        
        for player_id in players:
            player = User.query.get(player_id)
            if not player:
                continue
            
            trainings = TrainingSession.query.filter_by(player_id=player_id).all()
            if trainings:
                avg_score = sum(t.score for t in trainings) / len(trainings)
                total_rewards = sum(t.reward for t in trainings)
                session_count = len(trainings)
            else:
                avg_score = 0.0
                total_rewards = 0.0
                session_count = 0
            
            leaderboard.append({
                'player_id': player_id,
                'player_name': player.full_name,
                'avg_score': avg_score,
                'total_rewards': total_rewards,
                'session_count': session_count
            })
        
        leaderboard.sort(key=lambda x: x['avg_score'], reverse=True)
        for i, entry in enumerate(leaderboard, 1):
            entry['rank'] = i
        
        return jsonify({'leaderboard': leaderboard}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@club_bp.route('/<club_id>/toggle-active', methods=['PUT'])
@jwt_required()
def toggle_club_active(club_id):
    try:
        user_id = get_jwt_identity()
        club = CoachClub.query.get(club_id)
        if not club:
            return jsonify({'error': 'Club non trouvé'}), 404
        
        user = User.query.get(user_id)
        if club.coach_id != user_id and user.role != UserRole.ADMIN:
            return jsonify({'error': 'Accès non autorisé'}), 403
        
        club.is_active = not club.is_active
        club.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({'message': f'Club {"activé" if club.is_active else "désactivé"}'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

# ==================== ROUTES ENTRAÎNEMENT ====================



@training_bp.route('/analyze', methods=['POST'])
@jwt_required(optional=True)
def analyze_training():

    try:

        if "video" not in request.files:
            return jsonify({
                "error": "Vidéo manquante"
            }),400

        video=request.files["video"]

        training_type=request.form.get("type")

        if training_type is None:
            return jsonify({
                "error":"Type manquant"
            }),400

        filename=secure_filename(video.filename)

        temp_dir=tempfile.gettempdir()

        video_path=os.path.join(
            temp_dir,
            filename
        )

        video.save(video_path)
        ai_service = AIService()
        analysis=ai_service._analyze_with_video(
            video_path,
            training_type
        )

        os.remove(video_path)

        return jsonify({
        "status": "done",
        **analysis
        }), 200

    except Exception as e:

        import traceback
        traceback.print_exc()

        return jsonify({

            "status":"error",

            "error":str(e)

        }),500

@training_bp.route('/session', methods=['POST'])
@jwt_required()
def save_training_session():
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        required_fields = ['type', 'score', 'duration', 'level']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Champ {field} requis'}), 400
        
        training_type = TrainingType(data['type'])
        level = SkillLevel(data['level'])
        
        # Créer la session
        session = TrainingSession(
            id=str(uuid.uuid4()),
            player_id=user_id,
            type=training_type,
            score=data['score'],
            duration=data['duration'],
            level=level,
            reward=data.get('reward', 0.0),
            video_url=data.get('video_url'),
            metrics=data.get('metrics', {})
        )
        
        db.session.add(session)
        
        # Ajouter la récompense au wallet
        player = User.query.get(user_id)
        if player:
            player.wallet_balance += session.reward
            
            # Créer une transaction
            transaction = Transaction(
                id=str(uuid.uuid4()),
                user_id=user_id,
                amount=session.reward,
                type=TransactionType.REWARD,
                status=TransactionStatus.COMPLETED,
                description=f"Récompense pour entraînement {training_type.value}"
            )
            db.session.add(transaction)
        
        db.session.commit()
        
        return jsonify({
            'message': 'Session enregistrée',
            'session': session.to_dict(),
            'reward': session.reward
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@training_bp.route('/sessions', methods=['GET'])
@jwt_required()
def get_player_sessions():
    try:
        user_id = get_jwt_identity()
        training_type = request.args.get('type')
        
        query = TrainingSession.query.filter_by(player_id=user_id)
        if training_type:
            query = query.filter_by(type=TrainingType(training_type))
        
        sessions = query.order_by(TrainingSession.created_at.desc()).all()
        return jsonify({'sessions': [s.to_dict() for s in sessions]}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@training_bp.route('/stats', methods=['GET'])
@jwt_required()
def get_training_stats():
    try:
        user_id = get_jwt_identity()
        stats = TrainingService.get_training_statistics_by_type(user_id)
        return jsonify(stats), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ==================== ROUTES PAIEMENT ====================
@payment_bp.route('/process', methods=['POST'])
@jwt_required()
def process_payment():
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        required_fields = ['coach_id', 'club_id', 'amount']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Champ {field} requis'}), 400
        
        # Vérifier le joueur
        player = User.query.get(user_id)
        if not player:
            return jsonify({'error': 'Joueur non trouvé'}), 404
        
        if player.role != UserRole.PLAYER:
            return jsonify({'error': 'Seuls les joueurs peuvent payer'}), 400
        
        # Vérifier le club
        club = CoachClub.query.get(data['club_id'])
        if not club:
            return jsonify({'error': 'Club non trouvé'}), 404
        
        # Vérifier si le joueur est déjà dans le club
        current_players = club.current_players or []
        if user_id in current_players:
            return jsonify({'error': 'Vous êtes déjà dans ce club'}), 400
        
        # Vérifier les places disponibles
        if len(current_players) >= club.max_players:
            return jsonify({'error': 'Le club est complet'}), 400
        
        # Vérifier le solde
        if player.wallet_balance < data['amount']:
            return jsonify({'error': 'Solde insuffisant'}), 400
        
        # Créer la transaction
        transaction = Transaction(
            id=str(uuid.uuid4()),
            user_id=user_id,
            coach_id=data['coach_id'],
            club_id=data['club_id'],
            amount=data['amount'],
            type=TransactionType.PAYMENT,
            status=TransactionStatus.COMPLETED,
            description=data.get('description', f'Abonnement au club {club.club_name}')
        )
        
        # Débiter le joueur
        player.wallet_balance -= data['amount']
        
        # Créditer le coach
        coach = User.query.get(data['coach_id'])
        if coach:
            coach.wallet_balance = (coach.wallet_balance or 0) + data['amount']
        
        # ✅ AJOUTER LE JOUEUR AU CLUB
        current_players.append(user_id)
        club.current_players = current_players
        club.total_players = len(current_players)
        club.updated_at = datetime.utcnow()
        
        db.session.add(transaction)
        db.session.commit()
        
        # Récupérer les informations du joueur pour la réponse
        player_data = {
            'id': player.id,
            'full_name': player.full_name,
            'email': player.email,
            'phone': player.phone or '',
            'joined_date': club.updated_at.isoformat() if club.updated_at else None
        }
        
        return jsonify({
            'success': True,
            'message': 'Paiement effectué avec succès, vous êtes maintenant membre du club',
            'transaction': transaction.to_dict(),
            'new_balance': player.wallet_balance,
            'club': {
                'id': club.id,
                'club_name': club.club_name,
                'coach_name': coach.full_name if coach else 'Coach',
                'total_players': club.total_players,
                'current_players': club.current_players
            },
            'player': player_data
        }), 200
        
    except Exception as e:
        db.session.rollback()
        print(f"❌ Erreur payment: {e}")
        return jsonify({'error': str(e)}), 500

@payment_bp.route('/transactions', methods=['GET'])
@jwt_required()
def get_transactions():
    try:
        user_id = get_jwt_identity()
        transactions = Transaction.query.filter_by(user_id=user_id).order_by(
            Transaction.created_at.desc()
        ).all()
        return jsonify({
            'success': True,
            'transactions': [t.to_dict() for t in transactions]
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@club_bp.route('/<club_id>/players', methods=['GET'])
@jwt_required()
def get_club_players_list(club_id):
    try:
        user_id = get_jwt_identity()
        print(f"🔍 Récupération des joueurs du club {club_id}")
        
        club = CoachClub.query.get(club_id)
        if not club:
            return jsonify({
                'success': False,
                'error': 'Club non trouvé'
            }), 404
        
        user = User.query.get(user_id)
        if club.coach_id != user_id and user.role != UserRole.ADMIN:
            return jsonify({
                'success': False,
                'error': 'Accès non autorisé'
            }), 403
        
        players = []
        current_players = club.current_players or []
        print(f"👥 Joueurs trouvés: {current_players}")
        
        for player_id in current_players:
            player = User.query.get(player_id)
            if player:
                # ✅ Récupérer les sessions d'entraînement du joueur
                trainings = TrainingSession.query.filter_by(player_id=player_id).all()
                
                # ✅ Calculer les scores
                speed_scores = [t.score for t in trainings if t.type == TrainingType.SPEED]
                control_scores = [t.score for t in trainings if t.type == TrainingType.CONTROL_BALL]
                shoot_scores = [t.score for t in trainings if t.type == TrainingType.SHOOT]
                pass_scores = [t.score for t in trainings if t.type == TrainingType.PASS]
                
                speed_avg = sum(speed_scores) / len(speed_scores) if speed_scores else 0.0
                control_avg = sum(control_scores) / len(control_scores) if control_scores else 0.0
                shoot_avg = sum(shoot_scores) / len(shoot_scores) if shoot_scores else 0.0
                pass_avg = sum(pass_scores) / len(pass_scores) if pass_scores else 0.0
                
                total_score = speed_avg + control_avg + shoot_avg + pass_avg
                total_rewards = sum(t.reward for t in trainings) if trainings else 0.0
                
                # ✅ Déterminer le niveau
                avg_score = total_score / 4 if total_score > 0 else 0.0
                if avg_score >= 90:
                    level = 'expert'
                elif avg_score >= 75:
                    level = 'advanced'
                elif avg_score >= 50:
                    level = 'intermediate'
                else:
                    level = 'beginner'
                
                players.append({
                    'id': player.id,
                    'full_name': player.full_name,
                    'email': player.email,
                    'phone': player.phone or '',
                    'joined_date': club.updated_at.isoformat() if club.updated_at else None,
                    'speed_score': round(speed_avg, 2),
                    'control_ball_score': round(control_avg, 2),
                    'shoot_score': round(shoot_avg, 2),
                    'pass_score': round(pass_avg, 2),
                    'total_score': round(total_score, 2),
                    'total_rewards': round(total_rewards, 2),
                    'training_sessions_count': len(trainings),
                    'overall_level': level,
                    'progress_rate': 0.0  # À calculer si besoin
                })
        
        return jsonify({
            'success': True,
            'players': players,
            'total_players': len(players),
            'max_players': club.max_players
        }), 200
        
    except Exception as e:
        print(f"❌ Erreur get_club_players_list: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
# ==================== ROUTES STATISTIQUES ====================

@stats_bp.route('/player/<player_id>', methods=['GET'])
@jwt_required()
def get_player_stats(player_id):
    try:
        stats = PlayerStatsService.get_player_stats(player_id)
        return jsonify(stats.to_dict()), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@stats_bp.route('/club/<club_id>', methods=['GET'])
@jwt_required()
def get_club_stats(club_id):
    try:
        club = CoachClub.query.get(club_id)
        if not club:
            return jsonify({'error': 'Club non trouvé'}), 404
        
        players = club.current_players or []
        
        stats = {
            'total_players': len(players),
            'max_players': club.max_players,
            'available_slots': club.max_players - len(players),
            'budget': club.budget,
            'subscription_fee': club.subscription_fee,
            'rating': club.rating,
            'total_rewards': 0.0,
            'average_score': 0.0,
            'total_trainings': 0
        }
        
        for player_id in players:
            trainings = TrainingSession.query.filter_by(player_id=player_id).all()
            if trainings:
                stats['total_rewards'] += sum(t.reward for t in trainings)
                stats['average_score'] += sum(t.score for t in trainings) / len(trainings)
                stats['total_trainings'] += len(trainings)
        
        if players:
            stats['average_score'] /= len(players)
        
        return jsonify(stats), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@stats_bp.route('/player/<player_id>/progress', methods=['GET'])
@jwt_required()
def get_player_progress(player_id):
    try:
        days = int(request.args.get('days', 30))
        progress = PlayerStatsService.get_player_progress(player_id, days)
        return jsonify(progress), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@stats_bp.route('/player/<player_id>/achievements', methods=['GET'])
@jwt_required()
def get_player_achievements(player_id):
    try:
        achievements = PlayerStatsService.get_player_achievements(player_id)
        return jsonify({'achievements': achievements}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@stats_bp.route('/top-performers', methods=['GET'])
@jwt_required()
def get_top_performers():
    try:
        club_id = request.args.get('club_id')
        limit = int(request.args.get('limit', 10))
        top = PlayerStatsService.get_top_performers(club_id, limit)
        return jsonify({'top_performers': top}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@stats_bp.route('/player/<player_id>/recommendations', methods=['GET'])
@jwt_required()
def get_training_recommendations(player_id):
    try:
        recommendations = PlayerStatsService.get_training_recommendations(player_id)
        return jsonify({'recommendations': recommendations}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500