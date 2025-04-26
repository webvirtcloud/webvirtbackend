from django.urls import include, re_path
from rest_framework.urlpatterns import format_suffix_patterns

urlpatterns = [
    re_path(r"v1/?", include("api.v1.urls")),
]

urlpatterns = format_suffix_patterns(urlpatterns)
