from django.urls import re_path

from lbaas.views import LBaaSListAPI

urlpatterns = [
    re_path(r"$", LBaaSListAPI.as_view(), name="lbaas_list_api"),
    re_path(r"(?P<uuid>[0-9a-f-]+)/?$", LBaaSListAPI.as_view(), name="lbaas_data_api"),
]
