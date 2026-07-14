import os
from datetime import timedelta
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()

class Config:
    """Configuration principale de l'application"""
    
    # Clé secrète pour Flask
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production-12345'
    
    # Base de données
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///football.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = os.environ.get('SQLALCHEMY_ECHO', 'False').lower() == 'true'
    SQLALCHEMY_POOL_SIZE = int(os.environ.get('SQLALCHEMY_POOL_SIZE', 10))
    SQLALCHEMY_MAX_OVERFLOW = int(os.environ.get('SQLALCHEMY_MAX_OVERFLOW', 20))
    
    # JWT Configuration
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY') or 'jwt-secret-key-change-in-production-67890'
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=int(os.environ.get('JWT_ACCESS_TOKEN_EXPIRES_HOURS', 1)))
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=int(os.environ.get('JWT_REFRESH_TOKEN_EXPIRES_DAYS', 30)))
    JWT_TOKEN_LOCATION = ['headers']
    JWT_HEADER_NAME = 'Authorization'
    JWT_HEADER_TYPE = 'Bearer'
    
    # Upload Configuration
    UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER', 'uploads/videos')
    MAX_CONTENT_LENGTH = int(os.environ.get('MAX_CONTENT_LENGTH', 100 * 1024 * 1024))  # 100MB
    ALLOWED_EXTENSIONS = {'mp4', 'avi', 'mov', 'mkv', 'webm', 'mpg', 'mpeg'}
    MAX_VIDEO_DURATION = int(os.environ.get('MAX_VIDEO_DURATION', 300))  # 5 minutes
    
    # AI Configuration
    MODEL_PATH = os.environ.get('MODEL_PATH', 'models/ai_model.h5')
    CONFIDENCE_THRESHOLD = float(os.environ.get('CONFIDENCE_THRESHOLD', 0.6))
    AI_FEATURES_DIM = int(os.environ.get('AI_FEATURES_DIM', 10))
    
    # Payment Configuration
    MIN_REWARD = float(os.environ.get('MIN_REWARD', 0.5))
    MAX_REWARD = float(os.environ.get('MAX_REWARD', 10.0))
    DEFAULT_SUBSCRIPTION_FEE = float(os.environ.get('DEFAULT_SUBSCRIPTION_FEE', 50.0))
    DEFAULT_BUDGET = float(os.environ.get('DEFAULT_BUDGET', 10000.0))
    
    # CORS Configuration
    CORS_ORIGINS = os.environ.get('CORS_ORIGINS', 'http://localhost:3000,http://localhost:5000,http://localhost:8080,http://192.168.1.*').split(',')
    CORS_ALLOW_CREDENTIALS = True
    CORS_ALLOW_METHODS = ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS', 'PATCH']
    CORS_ALLOW_HEADERS = ['Content-Type', 'Authorization', 'X-Requested-With', 'Accept']
    
    # Email Configuration (pour les notifications)
    MAIL_SERVER = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
    MAIL_PORT = int(os.environ.get('MAIL_PORT', 587))
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'True').lower() == 'true'
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER', 'noreply@footballscout.com')
    
    # Application Configuration
    APP_NAME = os.environ.get('APP_NAME', 'AI Football Scout Wallet')
    APP_VERSION = os.environ.get('APP_VERSION', '1.0.0')
    ENVIRONMENT = os.environ.get('ENVIRONMENT', 'development')
    DEBUG = os.environ.get('DEBUG', 'True').lower() == 'true'
    
    # Pagination
    PAGE_SIZE = int(os.environ.get('PAGE_SIZE', 20))
    MAX_PAGE_SIZE = int(os.environ.get('MAX_PAGE_SIZE', 100))
    
    # Cache (optionnel)
    CACHE_TYPE = os.environ.get('CACHE_TYPE', 'simple')
    CACHE_DEFAULT_TIMEOUT = int(os.environ.get('CACHE_DEFAULT_TIMEOUT', 300))
    
    # Logging
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
    LOG_FILE = os.environ.get('LOG_FILE', 'app.log')
    LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    @staticmethod
    def init_app(app):
        """Initialisation de l'application avec la configuration"""
        # Créer les dossiers nécessaires
        os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)
        os.makedirs('models', exist_ok=True)
        
        # Configurer le logging
        import logging
        from logging.handlers import RotatingFileHandler
        
        if Config.ENVIRONMENT == 'production':
            # Configuration du logging en production
            handler = RotatingFileHandler(
                Config.LOG_FILE,
                maxBytes=10000000,
                backupCount=3
            )
            handler.setLevel(getattr(logging, Config.LOG_LEVEL))
            formatter = logging.Formatter(Config.LOG_FORMAT)
            handler.setFormatter(formatter)
            
            app.logger.addHandler(handler)
            app.logger.setLevel(getattr(logging, Config.LOG_LEVEL))
        else:
            # Logging en développement
            logging.basicConfig(
                level=getattr(logging, Config.LOG_LEVEL),
                format=Config.LOG_FORMAT
            )

class DevelopmentConfig(Config):
    """Configuration pour le développement"""
    DEBUG = True
    ENVIRONMENT = 'development'
    SQLALCHEMY_ECHO = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///football_dev.db'

class TestingConfig(Config):
    """Configuration pour les tests"""
    TESTING = True
    DEBUG = True
    ENVIRONMENT = 'testing'
    SQLALCHEMY_DATABASE_URI = os.environ.get('TEST_DATABASE_URL') or 'sqlite:///football_test.db'
    SQLALCHEMY_ECHO = False
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(minutes=5)
    
    # Désactiver les emails en test
    MAIL_SUPPRESS_SEND = True

class ProductionConfig(Config):
    """Configuration pour la production"""
    DEBUG = False
    ENVIRONMENT = 'production'
    SQLALCHEMY_ECHO = False
    
    # En production, utiliser une base de données plus robuste
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'postgresql://user:password@localhost/football'
    
    # Sécurité renforcée
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    
    # Rate limiting (optionnel)
    RATELIMIT_ENABLED = True
    RATELIMIT_DEFAULT = '100/hour'
    RATELIMIT_STORAGE_URL = 'memory://'

# Dictionnaire des configurations disponibles
config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}

# Fonction pour obtenir la configuration en fonction de l'environnement
def get_config():
    """Retourne la configuration appropriée selon l'environnement"""
    env = os.environ.get('FLASK_ENV', 'development')
    return config.get(env, DevelopmentConfig)