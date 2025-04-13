"""
Django production settings for WebVirtCloud project.

"""

from .base import *  # noqa: F403

# Django settings
DEBUG = False

try:
    from .local import *  # noqa: F403
except ImportError:
    pass
