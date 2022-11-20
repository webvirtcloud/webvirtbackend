from django.urls import include, re_path
from rest_framework.urlpatterns import format_suffix_patterns

from region.views import RegionListAPI

urlpatterns = [
    re_path(r"$", RegionListAPI.as_view(), name="region_list_api"),
]

urlpatterns = format_suffix_patterns(urlpatterns)
