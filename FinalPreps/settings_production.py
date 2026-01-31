"""Production settings wrapper for FinalPreps.
Import base settings and apply production-safe overrides. Use by setting
DJANGO_SETTINGS_MODULE=FinalPreps.settings_production
"""
from .settings import *  # noqa: F401,F403

# Explicitly ensure DEBUG is False in production
DEBUG = False

# Ensure SECRET_KEY is read from environment
SECRET_KEY = config('SECRET_KEY')

# Security defaults (can be overridden by env vars if needed)
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_SSL_REDIRECT = config('SECURE_SSL_REDIRECT', default=True, cast=bool)
SECURE_HSTS_SECONDS = config('SECURE_HSTS_SECONDS', default=31536000, cast=int)
SECURE_HSTS_INCLUDE_SUBDOMAINS = config('SECURE_HSTS_INCLUDE_SUBDOMAINS', default=True, cast=bool)
SECURE_HSTS_PRELOAD = config('SECURE_HSTS_PRELOAD', default=True, cast=bool)
