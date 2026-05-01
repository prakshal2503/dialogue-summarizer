"""
Django settings for Dialogue Summarizer Cloud Framework
"""
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

# ── Security ────────────────────────────────────────────────────────────────
SECRET_KEY = os.environ.get('SECRET_KEY', 'django-insecure-change-this-in-production-use-env-variable-xyz123')
DEBUG      = os.environ.get('DEBUG', 'False') == 'True'
ALLOWED_HOSTS = ['*']

CSRF_TRUSTED_ORIGINS = [
    'https://prakshal2503-dialogue-summarizer.hf.space',
]

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
    'whitenoise.middleware.WhiteNoiseMiddleware',  # ← added for static files
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

# ── MongoDB Configuration ────────────────────────────────────────────────────
MONGODB_URI = os.environ.get('MONGODB_URI', 'mongodb://localhost:27017/')
MONGODB_DATABASE = os.environ.get('MONGODB_DATABASE', 'dialogue_summarizer_db')

# ── Session Configuration ────────────────────────────────────────────────────
SESSION_ENGINE              = 'django.contrib.sessions.backends.db'
SESSION_COOKIE_AGE          = 3600
SESSION_COOKIE_SECURE       = not DEBUG  # True in production
SESSION_COOKIE_HTTPONLY     = True
SESSION_COOKIE_SAMESITE     = 'Lax'
SESSION_EXPIRE_AT_BROWSER_CLOSE = True

# ── Static files ─────────────────────────────────────────────────────────────
STATIC_URL   = '/static/'
STATIC_ROOT  = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [BASE_DIR / 'core' / 'static']
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'  # ← added

# ── Media files ──────────────────────────────────────────────────────────────
MEDIA_URL  = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# ── Model Paths ───────────────────────────────────────────────────────────────
MODEL_PATH       = os.environ.get('MODEL_PATH',       str(BASE_DIR / 'best_model'))
AUDIO_MODEL_PATH = os.environ.get('AUDIO_MODEL_PATH', str(BASE_DIR / 'audio_summarizer_model'))
VIDEO_MODEL_PATH = os.environ.get('VIDEO_MODEL_PATH', str(BASE_DIR / 'video_summarizer_model'))

# ── File Upload ───────────────────────────────────────────────────────────────
FILE_UPLOAD_MAX_MEMORY_SIZE = 100 * 1024 * 1024
DATA_UPLOAD_MAX_MEMORY_SIZE = 500 * 1024 * 1024
FILE_UPLOAD_TEMP_DIR        = None

ALLOWED_UPLOAD_EXTENSIONS = [
    '.txt', '.pdf', '.docx', '.doc',
    '.csv', '.json', '.jsonl',
    '.xlsx', '.xls', '.ods',
    '.pptx', '.ppt',
    '.md', '.rst', '.rtf',
    '.html', '.htm', '.xml',
    '.log', '.tsv',
]

# ── Security Settings ─────────────────────────────────────────────────────────
SECURE_BROWSER_XSS_FILTER   = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS             = 'DENY'
CSRF_COOKIE_HTTPONLY        = True

# ── reCAPTCHA ─────────────────────────────────────────────────────────────────
RECAPTCHA_PUBLIC_KEY  = os.environ.get('RECAPTCHA_PUBLIC_KEY',  '6LeIxAcTAAAAAJcZVRqyHh71UMIEGNQ_MXjiZKhI')
RECAPTCHA_PRIVATE_KEY = os.environ.get('RECAPTCHA_PRIVATE_KEY', '6LeIxAcTAAAAAGG-vFI1TnRWxMZNFuojJ4WifJWe')
RECAPTCHA_VERIFY_URL  = 'https://www.google.com/recaptcha/api/siteverify'

# ── Auth ──────────────────────────────────────────────────────────────────────
LOGIN_URL           = '/login/'
LOGIN_REDIRECT_URL  = '/dashboard/'
LOGOUT_REDIRECT_URL = '/login/'
MAX_LOGIN_ATTEMPTS  = 5
LOCKOUT_DURATION    = 900

# ── Admin ─────────────────────────────────────────────────────────────────────
ADMIN_USERNAME = os.environ.get('ADMIN_USERNAME', 'admin')
ADMIN_EMAIL    = os.environ.get('ADMIN_EMAIL',    'admin@dialoguesummarizer.com')

# ── Pagination ────────────────────────────────────────────────────────────────
ITEMS_PER_PAGE = 10

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ── Database (SQLite for Django sessions) ─────────────────────────────────────
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME'  : BASE_DIR / 'db_sessions.sqlite3',
    }
}

# ── Logging ───────────────────────────────────────────────────────────────────
LOGGING = {
    'version'                  : 1,
    'disable_existing_loggers' : False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'django': {
            'handlers' : ['console'],
            'level'    : 'INFO',
        },
        'core.security': {
            'handlers'  : ['console'],
            'level'     : 'WARNING',
            'propagate' : False,
        },
    },
}