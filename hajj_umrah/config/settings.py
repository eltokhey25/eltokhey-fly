"""
Django settings for the Hajj & Umrah site.
"""

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent


def _load_env_file(*paths):
    for path in paths:
        env_file = Path(path)
        if not env_file.exists():
            continue
        try:
            with open(env_file) as fh:
                for line in fh:
                    line = line.strip()
                    if not line or line.startswith('#') or '=' not in line:
                        continue
                    key, _, value = line.partition('=')
                    key = key.strip()
                    value = value.strip().strip('"').strip("'")
                    if key:
                        os.environ.setdefault(key, value)
        except OSError:
            continue


# Load local .env files (if present), without overriding real environment variables.
_load_env_file(BASE_DIR / '.env', BASE_DIR.parent / '.env')

# Load secret keys from the environment (or a local .env file). The fallback
# below is only for local development — set DJANGO_SECRET_KEY on the server.
SECRET_KEY = os.environ.get(
    'DJANGO_SECRET_KEY',
    'django-insecure-3*s#m957(lxzrsp()6j!f$pqp2(%$bul79+$^_c6=+jrq45d9z',
)

DEBUG = os.environ.get('DJANGO_DEBUG', 'True').lower() in {'1', 'true', 'yes', 'on'}

ALLOWED_HOSTS = os.environ.get(
    'DJANGO_ALLOWED_HOSTS', '127.0.0.1,localhost,testserver'
).split(',')

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sitemaps',
    'django.contrib.humanize',
    'core',
    'dashboard',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'core.context_processors.site_settings',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.environ.get('DJANGO_DB_PATH', str(BASE_DIR / 'db.sqlite3')),
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'ar-eg'

TIME_ZONE = 'Africa/Cairo'

USE_I18N = True

USE_TZ = True

STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [BASE_DIR / 'static']

# Serve PWA manifests with the right content type. WhiteNoise keeps its own
# media-type map (rather than Python's mimetypes), so register here.
WHITENOISE_MIMETYPES = {
    '.webmanifest': 'application/manifest+json',
    '.json': 'application/json',
}

STORAGES = {
    'default': {
        'BACKEND': 'django.core.files.storage.FileSystemStorage',
    },
    'staticfiles': {
        'BACKEND': 'whitenoise.storage.CompressedStaticFilesStorage',
    },
}

MEDIA_URL = '/media/'
MEDIA_ROOT = os.environ.get('DJANGO_MEDIA_ROOT', str(BASE_DIR / 'media'))
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# The default LocMemCache is per-process, so with `gunicorn --workers 2` each
# worker would keep its own rate-limit counters and double the effective cap.
# A file-backed cache is shared by every worker on the host.
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.filebased.FileBasedCache',
        'LOCATION': os.environ.get('DJANGO_CACHE_ROOT', str(BASE_DIR / 'cache')),
    }
}

EMAIL_HOST = os.environ.get('EMAIL_HOST', 'localhost')
EMAIL_PORT = int(os.environ.get('EMAIL_PORT', '587'))
EMAIL_USE_TLS = os.environ.get('EMAIL_USE_TLS', 'true').lower() in {'1', 'true', 'yes', 'on'}
EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD', '')
DEFAULT_FROM_EMAIL = os.environ.get(
    'DEFAULT_FROM_EMAIL', 'الطوخي للحج والعمرة <ahmedeltokhey55@gmail.com>'
)
ADMIN_NOTIFICATION_EMAIL = os.environ.get(
    'ADMIN_NOTIFICATION_EMAIL', 'meltokhey39@gmail.com'
)

# Use SMTP when credentials are configured, otherwise fall back to the console
# backend (prints emails to stdout) so local development and tests keep working.
EMAIL_BACKEND = os.environ.get(
    'EMAIL_BACKEND',
    'django.core.mail.backends.smtp.EmailBackend'
    if (EMAIL_HOST and EMAIL_HOST_PASSWORD and EMAIL_HOST_USER)
    else 'django.core.mail.backends.console.EmailBackend',
)

# Same-origin only so the dashboard can embed the public site in a live preview iframe
X_FRAME_OPTIONS = 'SAMEORIGIN'

# --- AI Chatbot (Groq) ---
GROQ_API_KEY = os.environ.get('GROQ_API_KEY', '')

# The chatbot widget posts to /api/chat/ from every visitor, so the endpoint is
# rate limited. These caps bound how much Groq spend a single visitor (or the
# site as a whole) can generate per hour.
CHAT_RATE_LIMIT_PER_HOUR = int(os.environ.get('CHAT_RATE_LIMIT_PER_HOUR', '20'))
CHAT_RATE_LIMIT_GLOBAL_PER_HOUR = int(
    os.environ.get('CHAT_RATE_LIMIT_GLOBAL_PER_HOUR', '300')
)

# Deployed behind a proxy (fly.io), so request.META['REMOTE_ADDR'] is the proxy,
# not the visitor. When this is on we read the client IP from the *right-most*
# X-Forwarded-For entry, which is the one our own proxy appends — a
# client-supplied X-Forwarded-For is only ever further left, so it cannot forge
# the value we key on. Turn off if the app is ever exposed without a proxy.
TRUST_X_FORWARDED_FOR = os.environ.get(
    'DJANGO_TRUST_X_FORWARDED_FOR', 'True'
).lower() in {'1', 'true', 'yes', 'on'}

