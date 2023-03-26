from django.urls import re_path

from image.views import ImageListAPI

urlpatterns = [
    re_path(r"$", ImageListAPI.as_view(), name="image_list_api"),
]
