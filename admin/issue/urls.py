from django.urls import re_path
from .views import (
    AdminIssueIndexView,
    AdminIssueVirtanceView,
    AdminIssueImageView,
    AdminIssueFirewallView,
    AdminIssueFloatIPView,
)


urlpatterns = [
    re_path(r"$", AdminIssueIndexView.as_view(), name="admin_issue_index"),
    re_path(r"image/?$", AdminIssueImageView.as_view(), name="admin_issue_image"),
    re_path(r"virtance/?$", AdminIssueVirtanceView.as_view(), name="admin_issue_virtance"),
    re_path(r"firewall/?$", AdminIssueFirewallView.as_view(), name="admin_issue_firewall"),
    re_path(r"floatingip/?$", AdminIssueFloatIPView.as_view(), name="admin_issue_floatip"),
]
