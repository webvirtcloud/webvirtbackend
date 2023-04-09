"""
Django develop settings for WebVirtCloud project.

"""
import socket

from .base import *


# Django settings
DEBUG = True

# Allowed hosts
ALLOWED_HOSTS = ["*"]

# Application definition
INSTALLED_APPS += [
    "drf_yasg",
    "corsheaders",
    "debug_toolbar",
]

# CORS settings
CORS_ORIGIN_ALLOW_ALL = True

# Security settings
SESSION_COOKIE_DOMAIN = os.environ.get("SESSION_COOKIE_DOMAIN", None)

# DebugToolBar
hostname, _, ips = socket.gethostbyname_ex(socket.gethostname())
INTERNAL_IPS = [ip[: ip.rfind(".")] + ".1" for ip in ips] + ["127.0.0.1", "localhost"]

# Middleware definition
MIDDLEWARE += [
    "corsheaders.middleware.CorsMiddleware",
    "debug_toolbar.middleware.DebugToolbarMiddleware",
]

# Static URL
STATIC_URL = "static/"

# noVNC settings
NOVNC_URL = "localhost"
NOVNC_PORT = 6080

try:
    from .local import *
except ImportError:
    pass
