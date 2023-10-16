from django.urls import re_path

from virtance.views import VirtanceListAPI, VirtanceDataAPI, VirtanceActionAPI, VirtanceConsoleAPI
from virtance.views import VirtanceMetricsCpuAPI, VirtanceMetricsNetAPI, VirtanceMetricsDiskAPI
from virtance.views import VirtanceBackupsAPI, VirtanceFirewallAPI, VirtanceSnapshotsAPI, VirtanceHistoryAPI

urlpatterns = [
    re_path(r"$", VirtanceListAPI.as_view(), name="virtance_list_api"),
    re_path(r"(?P<id>\d+)/?$", VirtanceDataAPI.as_view(), name="virtance_data_api"),
    re_path(r"(?P<id>\d+)/action/?$", VirtanceActionAPI.as_view(), name="virtance_action_api"),
    re_path(r"(?P<id>\d+)/history/?$", VirtanceHistoryAPI.as_view(), name="virtance_hisotry_api"),
    re_path(r"(?P<id>\d+)/backups/?$", VirtanceBackupsAPI.as_view(), name="virtance_backups_api"),
    re_path(r"(?P<id>\d+)/firewall/?$", VirtanceFirewallAPI.as_view(), name="virtance_firewall_api"),
    re_path(r"(?P<id>\d+)/snapshots/?$", VirtanceSnapshotsAPI.as_view(), name="virtance_snapshots_api"),
    re_path(r"(?P<id>\d+)/console/?$", VirtanceConsoleAPI.as_view(), name="virtance_console_api"),
    re_path(r"(?P<id>\d+)/metrics/cpu/?$", VirtanceMetricsCpuAPI.as_view(), name="virtance_metrics_cpu_api"),
    re_path(r"(?P<id>\d+)/metrics/net/?$", VirtanceMetricsNetAPI.as_view(), name="virtance_metrics_net_api"),
    re_path(r"(?P<id>\d+)/metrics/disk/?$", VirtanceMetricsDiskAPI.as_view(), name="virtance_metrics_disk_api"),
]
