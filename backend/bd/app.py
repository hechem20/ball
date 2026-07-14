from flask import Flask, jsonify
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from datetime import datetime
import os

from config import get_config, Config
from models import db
from routes.club_routes import auth_bp, club_bp, training_bp, payment_bp, stats_bp,wallet_bp
def create_app():
    app = Flask(__name__)
    app.config.from_object(get_config())
    
    # Initialisation
    Config.init_app(app)
    CORS(app,resources={r"/api/*": {"origins": "*"}})
    jwt = JWTManager(app)
    db.init_app(app)
    
    # Enregistrement des blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(club_bp)
    app.register_blueprint(training_bp)
    app.register_blueprint(payment_bp)
    app.register_blueprint(stats_bp)
    app.register_blueprint(wallet_bp)
    # Routes de base
    @app.route('/')
    def index():
        return jsonify({
            'name': 'AI Football Scout Wallet API',
            'version': '1.0.0',
            'status': 'running',
            'timestamp': datetime.utcnow().isoformat()
        })
    
    @app.route('/health')
    def health():
        return jsonify({
            'status': 'healthy',
            'database': 'connected',
            'timestamp': datetime.utcnow().isoformat()
        })
    
    # Création des tables
    with app.app_context():
        db.create_all()
        print("✅ Base de données initialisée")
    
    return app

if __name__ == '__main__':
    app = create_app()
    port = int(os.environ.get('PORT', 5000))
    host = os.environ.get('HOST', '0.0.0.0')
    app.run(host=host, port=port, debug=True)