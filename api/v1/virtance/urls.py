from django.urls import include, re_path

from virtance.views import VirtanceListAPI, VirtanceDataAPI, VirtanceActionAPI

urlpatterns = [
    re_path(r"$", VirtanceListAPI.as_view(), name="virtance_list_api"),
    re_path(r"(?P<id>\d+)/?$", VirtanceDataAPI.as_view(), name="virtance_data_api"),
    re_path(r"(?P<id>\d+)/action/?$", VirtanceActionAPI.as_view(), name="virtance_action_api"),
]
