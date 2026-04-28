"""
Django settings for Dialogue Summarizer Cloud Framework
"""
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
SECRET_KEY = 'django-insecure-change-this-in-production-use-env-variable-xyz123'
DEBUG = False  # Set to False in production
ALLOWED_HOSTS = ['localhost', '127.0.0.1', '0.0.0.0', '*']

# Application definition
INSTALLED_APPS = [
    'django.contrib.contenttypes',
    'django.contrib.staticfiles',
    'django.contrib.messages',
    'django.contrib.sessions',
    'core.apps.CoreConfig',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'core.middleware.LoginRequiredMiddleware',
    'core.middleware.SecurityHeadersMiddleware',
]

ROOT_URLCONF = 'dialogue_summarizer.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'core' / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.messages.context_processors.messages',
                'core.context_processors.sidebar_history',
            ],
        },
    },
]

WSGI_APPLICATION = 'dialogue_summarizer.wsgi.application'

# MongoDB Configuration
MONGODB_URI = os.environ.get('MONGODB_URI', 'mongodb://localhost:27017/')
MONGODB_DATABASE = os.environ.get('MONGODB_DATABASE', 'dialogue_summarizer_db')

# Session Configuration (stored in MongoDB)
SESSION_ENGINE = 'django.contrib.sessions.backends.db'
SESSION_COOKIE_AGE = 3600  # 1 hour
SESSION_COOKIE_SECURE = False  # Set True in production with HTTPS
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'
SESSION_EXPIRE_AT_BROWSER_CLOSE = True

# Static files
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [BASE_DIR / 'core' / 'static']

# Media files
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# ── T5 Model path ───────────────────────────────────────────────────────────
# Put your fine-tuned model files inside a folder called best_model/ next to
# manage.py. Override with: export MODEL_PATH=/absolute/path/to/model
MODEL_PATH = os.environ.get('MODEL_PATH', str(BASE_DIR / 'best_model'))

# ── Audio model path ────────────────────────────────────────────────────────
AUDIO_MODEL_PATH = os.environ.get('AUDIO_MODEL_PATH', str(BASE_DIR / 'audio_summarizer_model'))

# ── Video model path ────────────────────────────────────────────────────────
VIDEO_MODEL_PATH = os.environ.get('VIDEO_MODEL_PATH', str(BASE_DIR / 'video_summarizer_model'))

# File upload limits — no hard cap; limit only via DATA_UPLOAD_MAX_MEMORY_SIZE
# for request body safety. Actual file size is unrestricted at application level.
FILE_UPLOAD_MAX_MEMORY_SIZE = 100 * 1024 * 1024   # 100MB in-memory threshold
DATA_UPLOAD_MAX_MEMORY_SIZE = 500 * 1024 * 1024   # 500MB max request body
FILE_UPLOAD_TEMP_DIR = None  # Use system temp; Django streams large files to disk automatically

# All accepted upload extensions — add more here as needed
ALLOWED_UPLOAD_EXTENSIONS = [
    '.txt', '.pdf', '.docx', '.doc',
    '.csv', '.json', '.jsonl',
    '.xlsx', '.xls', '.ods',
    '.pptx', '.ppt',
    '.md', '.rst', '.rtf',
    '.html', '.htm', '.xml',
    '.log', '.tsv',
]

# Security Settings
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'
CSRF_COOKIE_HTTPONLY = True

# reCAPTCHA Keys (replace with your actual keys from https://www.google.com/recaptcha)
RECAPTCHA_PUBLIC_KEY = os.environ.get('RECAPTCHA_PUBLIC_KEY', '6LeIxAcTAAAAAJcZVRqyHh71UMIEGNQ_MXjiZKhI')  # Test key
RECAPTCHA_PRIVATE_KEY = os.environ.get('RECAPTCHA_PRIVATE_KEY', '6LeIxAcTAAAAAGG-vFI1TnRWxMZNFuojJ4WifJWe')  # Test key
RECAPTCHA_VERIFY_URL = 'https://www.google.com/recaptcha/api/siteverify'

# Login URL
LOGIN_URL = '/login/'
LOGIN_REDIRECT_URL = '/dashboard/'
LOGOUT_REDIRECT_URL = '/login/'

# Max failed login attempts before lockout
MAX_LOGIN_ATTEMPTS = 5
LOCKOUT_DURATION = 900  # 15 minutes in seconds

# Admin credentials (only one admin)
ADMIN_USERNAME = os.environ.get('ADMIN_USERNAME', 'admin')
ADMIN_EMAIL = os.environ.get('ADMIN_EMAIL', 'admin@dialoguesummarizer.com')

# Pagination
ITEMS_PER_PAGE = 10

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Dummy database for Django internals (sessions table workaround)
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db_sessions.sqlite3',
    }
}

# Logging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'file': {
            'level': 'WARNING',
            'class': 'logging.FileHandler',
            'filename': BASE_DIR / 'security.log',
        },
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'INFO',
        },
        'core.security': {
            'handlers': ['file', 'console'],
            'level': 'WARNING',
            'propagate': False,
        },
    },
}
