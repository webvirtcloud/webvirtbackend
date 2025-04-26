from django.urls import re_path

from .views import (
    AdminDBaaSDataView,
    AdminDBaaSDownlodPrivateKeyAction,
    AdminDBaaSIndexView,
    AdminDBaaSRecreateAction,
    AdminDBaaSResetEventAction,
)

urlpatterns = [
    re_path(r"$", AdminDBaaSIndexView.as_view(), name="admin_dbaas_index"),
    re_path(r"^(?P<pk>\d+)/$", AdminDBaaSDataView.as_view(), name="admin_dbaas_data"),
    re_path(r"^(?P<pk>\d+)/recreate/$", AdminDBaaSRecreateAction.as_view(), name="admin_dbaas_recreate"),
    re_path(r"^(?P<pk>\d+)/reset_event/$", AdminDBaaSResetEventAction.as_view(), name="admin_dbaas_reset_event"),
    re_path(
        r"^(?P<pk>\d+)/private_key/$",
        AdminDBaaSDownlodPrivateKeyAction.as_view(),
        name="admin_dbaas_download_private_key",
    ),
]
