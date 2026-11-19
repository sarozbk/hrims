"""
Client-specific overrides.

Imported last from horilla.settings.__init__ (after base + addons).
Override settings here; do NOT use ``from .base import *`` — that re-exports
base MEDIA_* values and wipes AWS S3 paths set by addons.py.

Examples:

    DEBUG = False
    ALLOWED_HOSTS = ["client.example.com"]
    WHITE_LABELLING = True
    DOC_BASE_URL = "https://www.horilla.com"

    # Extend lists via selective import (same list object as base):
    from .base import INSTALLED_APPS, MIDDLEWARE

    INSTALLED_APPS += ["client_portal"]
    MIDDLEWARE += ["client_portal.middleware.ClientTrackingMiddleware"]
"""

from .base import BASE_DIR, STATICFILES_DIRS, env

# Frontend date inputs use Bikram Sambat while storage and calculations remain
# Gregorian.
NEPALI_CALENDAR = True
TIME_ZONE = "Asia/Kathmandu"
DEBUG = True
WHITE_LABELLING = True

# Keep cookies secure by default. Set these to 0 only for an HTTP-only
# deployment, where browsers otherwise refuse to send CSRF/session cookies.
SESSION_COOKIE_SECURE = env.bool("SESSION_COOKIE_SECURE", default=True)
CSRF_COOKIE_SECURE = env.bool("CSRF_COOKIE_SECURE", default=True)

STATICFILES_DIRS += [
    ("nepali_datepicker", BASE_DIR / "horilla" / "settings" / "nepali_datepicker"),
]
