from django.urls import re_path
from .views import AdminVirtanceIndexView, AdminVirtanceDataView, AdminVirtanceConsoleView
from .views import AdminVirtanceResetEventAction, AdminVirtanceRecreateAction
from .views import AdminVirtancePowerOnAction, AdminVirtancePowerOffAction, AdminVirtancePowerCyrcleAction

urlpatterns = [
    re_path("$", AdminVirtanceIndexView.as_view(), name="admin_virtance_index"),
    re_path(r"^(?P<pk>\d+)/$", AdminVirtanceDataView.as_view(), name="admin_virtance_data"),
    re_path(r"^(?P<pk>\d+)/console/$", AdminVirtanceConsoleView.as_view(), name="admin_virtance_console"),
    re_path(r"^(?P<pk>\d+)/recreate/$", AdminVirtanceRecreateAction.as_view(), name="admin_virtance_recreate"),
    re_path(r"^(?P<pk>\d+)/power_on/$", AdminVirtancePowerOnAction.as_view(), name="admin_virtance_power_on"),
    re_path(r"^(?P<pk>\d+)/power_off/$", AdminVirtancePowerOffAction.as_view(), name="admin_virtance_power_off"),
    re_path(
        r"^(?P<pk>\d+)/power_cyrcle/$", AdminVirtancePowerCyrcleAction.as_view(), name="admin_virtance_power_cyrcle"
    ),
    re_path(r"^(?P<pk>\d+)/reset_event/$", AdminVirtanceResetEventAction.as_view(), name="admin_virtance_reset_event"),
]
