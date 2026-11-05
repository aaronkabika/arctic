"""
Configuration de l'application Arctic
"""
import os
from datetime import timedelta


class Config:
    """Configuration de base."""
    
    # Clé secrète
    SECRET_KEY = os.environ.get("ARCTIC_SECRET_KEY") or "dev_secret_key_change_in_production"
    
    # Base de données
    DATABASE = "arctic.db"
    
    # Fichiers uploadés
    UPLOAD_FOLDER = "uploads"
    MAX_CONTENT_LENGTH = 25 * 1024 * 1024  # 25 Mo
    ALLOWED_EXTENSIONS = {
        'image': {'jpg', 'jpeg', 'png', 'webp'},
        'audio': {'mp3', 'wav', 'ogg', 'm4a'},
        'document': {'pdf', 'doc', 'docx', 'txt'}
    }
    
    # Limites de taille par type de fichier (en Mo)
    FILE_SIZE_LIMITS = {
        'audio': 20,
        'image': 7,
        'document': 10
    }
    
    # Session
    SESSION_COOKIE_SECURE = False  # True en production avec HTTPS
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)
    
    # Pagination
    ITEMS_PER_PAGE = 12
    
    # Types d'œuvres autorisés
    ARTWORK_TYPES = {'musique', 'peinture', 'litterature', 'sculpture'}
    
    # Validation
    MIN_PASSWORD_LENGTH = 8
    MAX_PASSWORD_LENGTH = 20
    PHONE_LENGTH = 9
    MIN_AGE = 18


class DevelopmentConfig(Config):
    """Configuration de développement."""
    DEBUG = True
    TESTING = False


class ProductionConfig(Config):
    """Configuration de production."""
    DEBUG = False
    TESTING = False
    SESSION_COOKIE_SECURE = True


class TestingConfig(Config):
    """Configuration de test."""
    DEBUG = True
    TESTING = True
    DATABASE = ":memory:"


# Configuration par défaut
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}
