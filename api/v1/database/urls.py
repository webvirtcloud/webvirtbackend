from django.urls import re_path

from dbaas.views import DBaaSDataAPI, DBaaSListAPI

urlpatterns = [
    re_path(r"$", DBaaSListAPI.as_view(), name="dbaas_list_api"),
    re_path(r"(?P<uuid>[0-9a-f-]+)/?$", DBaaSDataAPI.as_view(), name="dbaas_data_api"),
]
