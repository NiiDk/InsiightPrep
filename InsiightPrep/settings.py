# InsightInnovations/settings.py
from pathlib import Path
from decouple import config
import os  # Keep os imported

BASE_DIR = Path(__file__).resolve().parent.parent

# ====================================================================
# SECURITY AND HOSTS
# ====================================================================
SECRET_KEY = config('SECRET_KEY')
DEBUG = config('DEBUG', default=False, cast=bool)

# Parse ALLOWED_HOSTS from config
allowed_hosts_str = config('ALLOWED_HOSTS', default='127.0.0.1,localhost')
ALLOWED_HOSTS = [host.strip() for host in allowed_hosts_str.split(',') if host.strip()]

# Add additional hosts
additional_hosts = [
    config('NGROK_TUNNEL', default='').replace('https://', '').replace('http://', '').split('/')[0],
    '.onrender.com',
    'insiightprep.onrender.com',
    config('RENDER_EXTERNAL_HOSTNAME', default=''),
]
for host in additional_hosts:
    if host and host not in ALLOWED_HOSTS:
        ALLOWED_HOSTS.append(host)

# ====================================================================
# API KEYS (No change)
# ====================================================================
PAYSTACK_PUBLIC_KEY = config('PAYSTACK_PUBLIC_KEY', default='')
PAYSTACK_SECRET_KEY = config('PAYSTACK_SECRET_KEY', default='')
ARKESEL_API_KEY = config('ARKESEL_API_KEY', default='')
CURRENCY_CODE = config('CURRENCY_CODE', default='GHS')

# ====================================================================
# EMAIL CONFIG (No change)
# ====================================================================
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = config('EMAIL_HOST', default='smtp.gmail.com')
EMAIL_PORT = config('EMAIL_PORT', default=587, cast=int)
EMAIL_USE_TLS = config('EMAIL_USE_TLS', default=True, cast=bool)
EMAIL_HOST_USER = config('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD')
DEFAULT_FROM_EMAIL = config('DEFAULT_FROM_EMAIL', default=EMAIL_HOST_USER)

# ====================================================================
# APPLICATIONS
# ====================================================================
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    
    # Cloudinary apps - MUST be before staticfiles
    'cloudinary_storage',
    'cloudinary',
    
    'django.contrib.staticfiles',
    
    # Your app
    'shop',
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

ROOT_URLCONF = 'InsiightPrep.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'shop.context_processors.current_year',
            ],
        },
    },
]

WSGI_APPLICATION = 'InsiightPrep.wsgi.application'

# ====================================================================
# DATABASE (No change)
# ====================================================================
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# ====================================================================
# PASSWORD VALIDATION (No change)
# ====================================================================
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# ====================================================================
# INTERNATIONALIZATION (No change)
# ====================================================================
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# ====================================================================
# STATIC FILES (Keep Whitenoise for production)
# ====================================================================
STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [BASE_DIR / 'static'] if (BASE_DIR / 'static').exists() else []

# ====================================================================
# MEDIA FILES - Now handled by Cloudinary in production
# ====================================================================
# These are kept for local development (when DEBUG=True)
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# ====================================================================
# CLOUDINARY CONFIGURATION
# ====================================================================
CLOUDINARY_STORAGE = {
    'CLOUD_NAME': config('CLOUDINARY_CLOUD_NAME'),
    'API_KEY': config('CLOUDINARY_API_KEY'),
    'API_SECRET': config('CLOUDINARY_API_SECRET'),
}

# ====================================================================
# STORAGE CONFIGURATION - Cloudinary for media, Whitenoise for static
# ====================================================================
STORAGES = {
    "default": {
        "BACKEND": "cloudinary_storage.storage.RawMediaCloudinaryStorage",  # For documents/PDFs
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ====================================================================
# WORKAROUND: Fix django-cloudinary-storage collectstatic compatibility issue
# The package incorrectly checks for the deprecated STATICFILES_STORAGE setting
# ====================================================================
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# ====================================================================
# SECURITY SETTINGS (FOR PRODUCTION)
# ====================================================================
if not DEBUG:
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    SECURE_HSTS_SECONDS = 31536000  # 1 year
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True