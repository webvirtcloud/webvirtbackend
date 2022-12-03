from django.urls import include, re_path

from virtance.views import VirtanceListAPI

urlpatterns = [
    re_path(r"$", VirtanceListAPI.as_view(), name="virtance_list_api"),
]
