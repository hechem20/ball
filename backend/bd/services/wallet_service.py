from datetime import datetime
from sqlalchemy import desc, func
from models import db, User, Transaction, TransactionType, TransactionStatus
import uuid

class WalletService:
    @staticmethod
    def get_balance(user_id):
        """Récupère le solde du wallet d'un utilisateur"""
        try:
            user = User.query.get(user_id)
            if not user:
                raise ValueError("Utilisateur non trouvé")
            return user.wallet_balance or 0.0
        except Exception as e:
            print(f"❌ Erreur get_balance: {e}")
            return 0.0
    
    @staticmethod
    def get_transactions(user_id, limit=None, transaction_type=None, status=None):
        """Récupère les transactions d'un utilisateur"""
        try:
            query = Transaction.query.filter_by(user_id=user_id)
            
            if transaction_type:
                query = query.filter_by(type=TransactionType(transaction_type))
            if status:
                query = query.filter_by(status=TransactionStatus(status))
            
            query = query.order_by(desc(Transaction.created_at))
            
            if limit:
                query = query.limit(limit)
            
            return query.all()
        except Exception as e:
            print(f"❌ Erreur get_transactions: {e}")
            return []
    
    @staticmethod
    def add_reward(user_id, amount, description=None):
        """Ajoute une récompense au wallet de l'utilisateur"""
        try:
            if amount <= 0:
                raise ValueError("Le montant doit être positif")
            
            user = User.query.get(user_id)
            if not user:
                raise ValueError("Utilisateur non trouvé")
            
            # Mettre à jour le solde
            user.wallet_balance = (user.wallet_balance or 0) + amount
            
            # Créer la transaction
            transaction = Transaction(
                id=str(uuid.uuid4()),
                user_id=user_id,
                amount=amount,
                type=TransactionType.REWARD,
                status=TransactionStatus.COMPLETED,
                description=description or "Récompense entraînement",
                created_at=datetime.utcnow()
            )
            
            db.session.add(transaction)
            db.session.commit()
            
            return {
                'balance': user.wallet_balance,
                'transaction': transaction.to_dict()
            }
        except Exception as e:
            db.session.rollback()
            print(f"❌ Erreur add_reward: {e}")
            raise e
    
    @staticmethod
    def deduct_amount(user_id, amount, description=None, coach_id=None, club_id=None):
        """Déduit un montant du wallet de l'utilisateur"""
        try:
            if amount <= 0:
                raise ValueError("Le montant doit être positif")
            
            user = User.query.get(user_id)
            if not user:
                raise ValueError("Utilisateur non trouvé")
            
            if (user.wallet_balance or 0) < amount:
                raise ValueError("Solde insuffisant")
            
            # Mettre à jour le solde
            user.wallet_balance = (user.wallet_balance or 0) - amount
            
            # Créer la transaction
            transaction = Transaction(
                id=str(uuid.uuid4()),
                user_id=user_id,
                coach_id=coach_id,
                club_id=club_id,
                amount=amount,
                type=TransactionType.PAYMENT,
                status=TransactionStatus.COMPLETED,
                description=description or "Paiement service",
                created_at=datetime.utcnow()
            )
            
            db.session.add(transaction)
            db.session.commit()
            
            return {
                'balance': user.wallet_balance,
                'transaction': transaction.to_dict()
            }
        except Exception as e:
            db.session.rollback()
            print(f"❌ Erreur deduct_amount: {e}")
            raise e
    
    @staticmethod
    def transfer_amount(from_user_id, to_user_id, amount, description=None):
        """Transfère un montant entre deux utilisateurs"""
        try:
            if amount <= 0:
                raise ValueError("Le montant doit être positif")
            
            # Vérifier les utilisateurs
            from_user = User.query.get(from_user_id)
            if not from_user:
                raise ValueError("Utilisateur source non trouvé")
            
            to_user = User.query.get(to_user_id)
            if not to_user:
                raise ValueError("Utilisateur destinataire non trouvé")
            
            if (from_user.wallet_balance or 0) < amount:
                raise ValueError("Solde insuffisant")
            
            # Déduire du source
            from_user.wallet_balance = (from_user.wallet_balance or 0) - amount
            
            # Ajouter au destinataire
            to_user.wallet_balance = (to_user.wallet_balance or 0) + amount
            
            # Créer les transactions
            transaction_id = str(uuid.uuid4())
            
            # Transaction source (débit)
            from_transaction = Transaction(
                id=transaction_id + "_from",
                user_id=from_user_id,
                amount=amount,
                type=TransactionType.PAYMENT,
                status=TransactionStatus.COMPLETED,
                description=description or f"Transfert vers {to_user.full_name}",
                created_at=datetime.utcnow()
            )
            
            # Transaction destination (crédit)
            to_transaction = Transaction(
                id=transaction_id + "_to",
                user_id=to_user_id,
                amount=amount,
                type=TransactionType.REWARD,
                status=TransactionStatus.COMPLETED,
                description=description or f"Transfert de {from_user.full_name}",
                created_at=datetime.utcnow()
            )
            
            db.session.add(from_transaction)
            db.session.add(to_transaction)
            db.session.commit()
            
            return {
                'from_balance': from_user.wallet_balance,
                'to_balance': to_user.wallet_balance,
                'transaction_id': transaction_id
            }
        except Exception as e:
            db.session.rollback()
            print(f"❌ Erreur transfer_amount: {e}")
            raise e
    
    @staticmethod
    def refund_transaction(transaction_id, user_id):
        """Rembourse une transaction"""
        try:
            transaction = Transaction.query.get(transaction_id)
            if not transaction:
                raise ValueError("Transaction non trouvée")
            
            if transaction.user_id != user_id:
                raise ValueError("Accès non autorisé")
            
            if transaction.status != TransactionStatus.COMPLETED:
                raise ValueError("La transaction n'est pas remboursable")
            
            if transaction.type != TransactionType.PAYMENT:
                raise ValueError("Seules les transactions de paiement peuvent être remboursées")
            
            # Rembourser l'utilisateur
            user = User.query.get(user_id)
            if user:
                user.wallet_balance = (user.wallet_balance or 0) + transaction.amount
            
            # Mettre à jour le statut de la transaction
            transaction.status = TransactionStatus.REFUNDED
            transaction.updated_at = datetime.utcnow()
            
            # Créer la transaction de remboursement
            refund_transaction = Transaction(
                id=str(uuid.uuid4()),
                user_id=user_id,
                amount=transaction.amount,
                type=TransactionType.REFUND,
                status=TransactionStatus.COMPLETED,
                description=f"Remboursement de {transaction.description}",
                created_at=datetime.utcnow()
            )
            
            db.session.add(refund_transaction)
            db.session.commit()
            
            return {
                'balance': user.wallet_balance if user else 0,
                'refund_transaction': refund_transaction.to_dict()
            }
        except Exception as e:
            db.session.rollback()
            print(f"❌ Erreur refund_transaction: {e}")
            raise e
    
    @staticmethod
    def get_transaction_summary(user_id):
        """Récupère un résumé des transactions de l'utilisateur"""
        try:
            user = User.query.get(user_id)
            if not user:
                raise ValueError("Utilisateur non trouvé")
            
            # Statistiques par type
            stats_by_type = {}
            for type_enum in TransactionType:
                count = Transaction.query.filter_by(
                    user_id=user_id,
                    type=type_enum,
                    status=TransactionStatus.COMPLETED
                ).count()
                
                total = db.session.query(func.sum(Transaction.amount)).filter(
                    Transaction.user_id == user_id,
                    Transaction.type == type_enum,
                    Transaction.status == TransactionStatus.COMPLETED
                ).scalar() or 0.0
                
                stats_by_type[type_enum.value] = {
                    'count': count,
                    'total': float(total)
                }
            
            # Dernières transactions
            recent_transactions = Transaction.query.filter_by(
                user_id=user_id
            ).order_by(desc(Transaction.created_at)).limit(5).all()
            
            return {
                'balance': user.wallet_balance or 0.0,
                'stats_by_type': stats_by_type,
                'recent_transactions': [t.to_dict() for t in recent_transactions],
                'total_transactions': Transaction.query.filter_by(user_id=user_id).count()
            }
        except Exception as e:
            print(f"❌ Erreur get_transaction_summary: {e}")
            return {
                'balance': 0.0,
                'stats_by_type': {},
                'recent_transactions': [],
                'total_transactions': 0
            }
    
    @staticmethod
    def get_coach_earnings(coach_id, club_id=None):
        """Récupère les gains d'un coach"""
        try:
            query = Transaction.query.filter_by(
                coach_id=coach_id,
                type=TransactionType.PAYMENT,
                status=TransactionStatus.COMPLETED
            )
            
            if club_id:
                query = query.filter_by(club_id=club_id)
            
            total_earnings = db.session.query(func.sum(Transaction.amount)).filter(
                Transaction.coach_id == coach_id,
                Transaction.type == TransactionType.PAYMENT,
                Transaction.status == TransactionStatus.COMPLETED
            ).scalar() or 0.0
            
            # Par joueur
            player_earnings = db.session.query(
                Transaction.user_id,
                func.sum(Transaction.amount).label('total')
            ).filter(
                Transaction.coach_id == coach_id,
                Transaction.type == TransactionType.PAYMENT,
                Transaction.status == TransactionStatus.COMPLETED
            ).group_by(Transaction.user_id).all()
            
            return {
                'total_earnings': float(total_earnings),
                'player_earnings': [
                    {
                        'player_id': result.user_id,
                        'total': float(result.total)
                    } for result in player_earnings
                ],
                'transaction_count': query.count()
            }
        except Exception as e:
            print(f"❌ Erreur get_coach_earnings: {e}")
            return {
                'total_earnings': 0.0,
                'player_earnings': [],
                'transaction_count': 0
            }
    
    @staticmethod
    def get_player_payments_history(player_id, coach_id=None):
        """Récupère l'historique des paiements d'un joueur"""
        try:
            query = Transaction.query.filter_by(
                user_id=player_id,
                type=TransactionType.PAYMENT,
                status=TransactionStatus.COMPLETED
            )
            
            if coach_id:
                query = query.filter_by(coach_id=coach_id)
            
            return query.order_by(desc(Transaction.created_at)).all()
        except Exception as e:
            print(f"❌ Erreur get_player_payments_history: {e}")
            return []