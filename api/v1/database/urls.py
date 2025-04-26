from django.urls import re_path

from dbaas.views import DBaaSDataAPI, DBaaSListAPI, DBaaSBackupsAPI, DBaaSSnapshotsAPI, DBaaSSnapshotAPI

urlpatterns = [
    re_path(r"$", DBaaSListAPI.as_view(), name="dbaas_list_api"),
    re_path(r"(?P<uuid>[0-9a-f-]+)/?$", DBaaSDataAPI.as_view(), name="dbaas_data_api"),
    re_path(r"(?P<uuid>[0-9a-f-]+)/backups/?$", DBaaSBackupsAPI.as_view(), name="dbaas_backups_api"),
    re_path(r"(?P<uuid>[0-9a-f-]+)/snapshots/?$", DBaaSSnapshotsAPI.as_view(), name="dbaas_snapshots_api"),
    re_path(
        r"(?P<uuid>[0-9a-f-]+)/snapshots/(?P<pk>[0-9a-f-]+)/?$", DBaaSSnapshotAPI.as_view(), name="dbaas_snapshot_api"
    ),
]
