from django.urls import re_path

from firewall.views import FirewallListAPI, FirewallDataAPI, FirewallRuleAPI, FirewallVirtanceAPI

urlpatterns = [
    re_path(r"$", FirewallListAPI.as_view(), name="firewall_list_api"),
    re_path(r"(?P<uuid>[0-9a-f-]+)/?$", FirewallDataAPI.as_view(), name="firewall_data_api"),
    re_path(r"(?P<uuid>[0-9a-f-]+)/rules/?$", FirewallRuleAPI.as_view(), name="firewall_rule_api"),
    re_path(r"(?P<uuid>[0-9a-f-]+)/virtances/?$", FirewallVirtanceAPI.as_view(), name="firewall_virtance_api"),
]
