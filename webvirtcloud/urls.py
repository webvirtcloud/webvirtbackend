"""
WebVirtCloud URL Configuration
"""
from django.conf import settings
from django.urls import include, path, re_path


urlpatterns = [
    re_path(r"", include("singlepage.urls")),
    re_path(r"account/", include("account.urls")),
]

if settings.DEBUG:
    import debug_toolbar

    urlpatterns += [
        path("__debug__/", include("debug_toolbar.urls")),
    ]
