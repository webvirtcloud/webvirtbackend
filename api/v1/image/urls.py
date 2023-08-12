from django.urls import re_path
from image.views import ImageListAPI, ImageDataAPI, ImageActionAPI, ImageSnapshotsAPI

urlpatterns = [
    re_path(r"$", ImageListAPI.as_view(), name="image_list_api"),
    re_path(r"snapshots/?$", ImageSnapshotsAPI.as_view(), name="image_snapshot_list_api"),
    re_path(r"(?P<id>\d+)/?$", ImageDataAPI.as_view(), name="image_data_api"),
    re_path(r"(?P<id>\d+)/action/?$", ImageActionAPI.as_view(), name="image_action_api"),
]
