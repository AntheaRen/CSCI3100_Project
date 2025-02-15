import os

class Config:
    # Database configuration
    BASEDIR = os.path.abspath(os.path.dirname(__file__))
    SQLITE_DB_PATH = os.path.join(BASEDIR, 'database', 'artify.db')
    SQLALCHEMY_DATABASE_URI = f'sqlite:///{SQLITE_DB_PATH}'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Security configuration
    SECRET_KEY = 'your-secret-key-here'  # Change this in production
    
    # API configuration
    API_PREFIX = '/api/v1' 