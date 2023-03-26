from django.urls import re_path

from size.views import SizeListAPI

urlpatterns = [
    re_path(r"$", SizeListAPI.as_view(), name="size_list_api"),
]
