"""
WebVirtCloud URL Configuration
"""
from django.conf import settings
from django.urls import include, path, re_path

urlpatterns = [
    re_path(r'api/(?P<version>[v1|v2]+)/', include('account.urls')),
]

if settings.DEBUG:
    import debug_toolbar

    urlpatterns += [
        path('__debug__/', include('debug_toolbar.urls')),
    ]
