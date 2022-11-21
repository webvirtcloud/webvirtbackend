from django.urls import include, re_path
from rest_framework.urlpatterns import format_suffix_patterns

from image.views import ImageListAPI

urlpatterns = [
    re_path(r"$", ImageListAPI.as_view(), name="image_list_api"),
]

urlpatterns = format_suffix_patterns(urlpatterns)
