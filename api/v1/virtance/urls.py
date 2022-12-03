from django.urls import include, re_path
from rest_framework.urlpatterns import format_suffix_patterns

from virtance.views import VirtanceListAPI

urlpatterns = [
    re_path(r"$", VirtanceListAPI.as_view(), name="virtance_list_api"),
]

urlpatterns = format_suffix_patterns(urlpatterns)
