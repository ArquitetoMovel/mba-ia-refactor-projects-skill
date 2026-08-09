import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    SECRET_KEY = os.getenv('SECRET_KEY', 'change-me-in-production')
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'sqlite:///tasks.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    DEBUG = os.getenv('FLASK_DEBUG', '0') == '1'
    HOST = os.getenv('HOST', '0.0.0.0')
    PORT = int(os.getenv('PORT', '5000'))

    SMTP_HOST = os.getenv('SMTP_HOST', '')
    SMTP_PORT = int(os.getenv('SMTP_PORT', '587'))
    SMTP_USER = os.getenv('SMTP_USER', '')
    SMTP_PASSWORD = os.getenv('SMTP_PASSWORD', '')
    SMTP_ENABLED = os.getenv('SMTP_ENABLED', '0') == '1'

    TOKEN_MAX_AGE_SECONDS = int(os.getenv('TOKEN_MAX_AGE_SECONDS', '86400'))

    VALID_STATUSES = ('pending', 'in_progress', 'done', 'cancelled')
    VALID_ROLES = ('user', 'admin', 'manager')
    MIN_TITLE_LENGTH = 3
    MAX_TITLE_LENGTH = 200
    MIN_PASSWORD_LENGTH = 8
    DEFAULT_PRIORITY = 3
    DEFAULT_COLOR = '#000000'
