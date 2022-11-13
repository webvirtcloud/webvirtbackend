"""
WebVirtCloud URL Configuration
"""
from django.conf import settings
from django.urls import include, path, re_path
from webvirtcloud.views import app_exception_handler404, app_exception_handler500


handler404 = app_exception_handler404
handler500 = app_exception_handler500


urlpatterns = [
    re_path(r"", include("singlepage.urls")),
    re_path(r"account/", include("account.urls")),
    re_path(r"api/", include("api.urls")),
]

if settings.DEBUG:
    import debug_toolbar
    from django.views.generic import TemplateView
    from rest_framework import permissions
    from rest_framework.schemas import get_schema_view

    urlpatterns += [
        path(
            "openapi/",
            get_schema_view(
                title="WebVirtCloud",
                description="WebVirtCloud API documentation",
                version="v1",
                public=True,
                # patterns=[path('api/', include('api.urls')), ],
                permission_classes=(permissions.AllowAny,),
            ),
            name="openapi-schema",
        ),
        # Swagger
        path(
            "swagger-ui/",
            TemplateView.as_view(
                template_name="openapi/swagger-ui.html", extra_context={"schema_url": "openapi-schema"}
            ),
            name="swagger-ui",
        ),
        # ReDoc
        path(
            "redoc/",
            TemplateView.as_view(template_name="openapi/redoc.html", extra_context={"schema_url": "openapi-schema"}),
            name="redoc",
        ),
        # Debug Toolbar
        path("__debug__/", include("debug_toolbar.urls")),
    ]
