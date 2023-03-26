"""
Django production settings for WebVirtCloud project.

"""
from .base import *

# Django settings
DEBUG = False
ADMIN_ENABLED = True

# Staic files
STATIC_URL = "https://cloud-assets.webvirt.cloud/"

try:
    from .local import *
except ImportError:
    pass
