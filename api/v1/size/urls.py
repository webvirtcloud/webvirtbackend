from django.urls import include, re_path
from rest_framework.urlpatterns import format_suffix_patterns

from size.views import SizeListAPI

urlpatterns = [
    re_path(r"$", SizeListAPI.as_view(), name="size_list_api"),
]

urlpatterns = format_suffix_patterns(urlpatterns)
