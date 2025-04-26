from django.urls import re_path

from .views import AdminFirewallDataView, AdminFirewallIndexView, AdminFirewallResetEventAction

urlpatterns = [
    re_path(r"$", AdminFirewallIndexView.as_view(), name="admin_firewall_index"),
    re_path(r"^(?P<pk>\d+)/$", AdminFirewallDataView.as_view(), name="admin_firewall_data"),
    re_path(r"^(?P<pk>\d+)/reset_event/$", AdminFirewallResetEventAction.as_view(), name="admin_firewall_reset_event"),
]
