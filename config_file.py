# config.py - Configuration settings for Healthcare AI Assistant

import os
from dataclasses import dataclass
from typing import Set

@dataclass
class Config:
    """Base configuration class"""
    
    # API Keys
    OPENAI_API_KEY: str = os.getenv('OPENAI_API_KEY', '')
    
    # Application Settings
    SECRET_KEY: str = os.getenv('SECRET_KEY', 'your-secret-key-change-in-production')
    DEBUG: bool = os.getenv('DEBUG', 'False').lower() == 'true'
    
    # File Upload Settings
    UPLOAD_FOLDER: str = os.getenv('UPLOAD_FOLDER', 'uploads')
    MAX_FILE_SIZE: int = int(os.getenv('MAX_FILE_SIZE', '16777216'))  # 16MB
    ALLOWED_EXTENSIONS: Set[str] = {'txt', 'pdf', 'docx', 'csv'}
    
    # Database Settings
    VECTOR_DB_PATH: str = os.getenv('VECTOR_DB_PATH', 'healthcare_vectordb')
    
    # AI Model Settings
    CHUNK_SIZE: int = int(os.getenv('CHUNK_SIZE', '1000'))
    CHUNK_OVERLAP: int = int(os.getenv('CHUNK_OVERLAP', '200'))
    MEMORY_WINDOW: int = int(os.getenv('MEMORY_WINDOW', '10'))
    TEMPERATURE: float = float(os.getenv('TEMPERATURE', '0.1'))
    
    # OpenAI Model Selection
    LLM_MODEL: str = os.getenv('LLM_MODEL', 'gpt-3.5-turbo-instruct')
    EMBEDDING_MODEL: str = os.getenv('EMBEDDING_MODEL', 'text-embedding-ada-002')
    
    # Logging Settings
    LOG_LEVEL: str = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FILE: str = os.getenv('LOG_FILE', 'healthcare_ai.log')

@dataclass 
class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG: bool = True

@dataclass
class ProductionConfig(Config):
    """Production configuration"""
    DEBUG: bool = False
    
    # Security Settings for Production
    SECURE_SSL_REDIRECT: bool = True
    SESSION_COOKIE_SECURE: bool = True
    SESSION_COOKIE_HTTPONLY: bool = True
    SESSION_COOKIE_SAMESITE: str = 'Lax'

@dataclass
class TestingConfig(Config):
    """Testing configuration"""
    TESTING: bool = True
    VECTOR_DB_PATH: str = 'test_vectordb'
    UPLOAD_FOLDER: str = 'test_uploads'

# Configuration mapping
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}

def get_config(env_name: str = None) -> Config:
    """Get configuration based on environment"""
    if env_name is None:
        env_name = os.getenv('FLASK_ENV', 'default')
    
    return config.get(env_name, config['default'])()
