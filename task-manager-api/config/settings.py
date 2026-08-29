import os

from dotenv import load_dotenv

load_dotenv()


class Settings:
    WEAK_SECRETS = frozenset({'', 'change-me-in-production', 'dev-secret-key-change-in-prod'})
    SECRET_KEY = os.getenv('SECRET_KEY')
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
    AUTH_TOKEN_SALT = 'task-manager-auth'

    STATUS_PENDING = 'pending'
    STATUS_IN_PROGRESS = 'in_progress'
    STATUS_DONE = 'done'
    STATUS_CANCELLED = 'cancelled'
    VALID_STATUSES = (STATUS_PENDING, STATUS_IN_PROGRESS, STATUS_DONE, STATUS_CANCELLED)
    NON_OVERDUE_STATUSES = (STATUS_DONE, STATUS_CANCELLED)

    ROLE_USER = 'user'
    ROLE_ADMIN = 'admin'
    ROLE_MANAGER = 'manager'
    VALID_ROLES = (ROLE_USER, ROLE_ADMIN, ROLE_MANAGER)

    MIN_PASSWORD_LENGTH = 8
    MIN_TITLE_LENGTH = 3
    MAX_TITLE_LENGTH = 200
    MAX_NAME_LENGTH = 100
    MIN_PRIORITY = 1
    MAX_PRIORITY = 5
    HIGH_PRIORITY_MAX = 2
    DEFAULT_PRIORITY = 3
    DEFAULT_STATUS = STATUS_PENDING
    DEFAULT_ROLE = ROLE_USER
    DEFAULT_COLOR = '#000000'

    DEFAULT_PER_PAGE = int(os.getenv('DEFAULT_PER_PAGE', '20'))
    MAX_PER_PAGE = int(os.getenv('MAX_PER_PAGE', '100'))
