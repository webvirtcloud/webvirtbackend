"""
Django production settings for WebVirtCloud project.

"""
try:
    from .base import *
except ImportError:
    pass


# Django settings
DEBUG = False
ADMIN_ENABLED = True

try:
    from .local import *
except ImportError:
    pass
