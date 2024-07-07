from django.urls import re_path
from .views import (
    AdminLBaaSIndexView,
    AdminLBaaSDataView,
    AdminLBaaSResetEventAction,
    AdminLBaaSRecreateAction,
    AdminLBaaSDownlodPrivateKeyAction,
)

urlpatterns = [
    re_path(r"$", AdminLBaaSIndexView.as_view(), name="admin_lbaas_index"),
    re_path(r"^(?P<pk>\d+)/$", AdminLBaaSDataView.as_view(), name="admin_lbaas_data"),
    re_path(r"^(?P<pk>\d+)/recreate/$", AdminLBaaSRecreateAction.as_view(), name="admin_lbaas_recreate"),
    re_path(r"^(?P<pk>\d+)/reset_event/$", AdminLBaaSResetEventAction.as_view(), name="admin_lbaas_reset_event"),
    re_path(
        r"^(?P<pk>\d+)/private_key/$",
        AdminLBaaSDownlodPrivateKeyAction.as_view(),
        name="admin_lbaas_download_private_key",
    ),
]
