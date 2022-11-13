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
    from drf_yasg import openapi
    from drf_yasg.views import get_schema_view
    from rest_framework import permissions
    from django.views.generic import TemplateView

    schema_view = get_schema_view(  # new
        openapi.Info(
            title="WebVirtCloud API",
            default_version='v1',
            description="WebVirtCloud project for managing KVM virtual machines",
            terms_of_service="https://www.google.com/policies/terms/",
            contact=openapi.Contact(email="license@webvirt.cloud"),
            license=openapi.License(name="Apache2 License"),
        ),
        public=True,
        patterns=[path('api/', include('api.urls')), ],
        permission_classes=(permissions.AllowAny,),
    )

    urlpatterns += [
        # Swagger
        path('swagger-ui/', TemplateView.as_view(
                template_name='swagger-ui.html',
                extra_context={'schema_url': 'openapi-schema'}
            ),
            name='swagger-ui'),
        re_path(r'^swagger(?P<format>\.json|\.yaml)$',
            schema_view.without_ui(cache_timeout=0),
            name='schema-json'),

        # ReDoc
        path('redoc/', TemplateView.as_view(
            template_name='redoc.html',
            extra_context={'schema_url':'openapi-schema'}
        ), name='redoc'),     
     
        # Debug Toolbar
        path("__debug__/", include("debug_toolbar.urls")),
    ]
