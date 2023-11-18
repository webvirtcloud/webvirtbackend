from django.urls import re_path
from .views import (
    AdminIssueIndexView, 
    AdminIssueVirtanceView, 
    AdminIssueImageView, 
    AdminIssueFirewallView, 
    AdminIssueFloatIPView
)


urlpatterns = [
    re_path("$", AdminIssueIndexView.as_view(), name="admin_issue_index"),
    re_path("image/?$", AdminIssueImageView.as_view(), name="admin_issue_image"),
    re_path("virtance/?$", AdminIssueVirtanceView.as_view(), name="admin_issue_virtance"),
    re_path("firewall/?$", AdminIssueFirewallView.as_view(), name="admin_issue_firewall"),
    re_path("floatingip/?$", AdminIssueFloatIPView.as_view(), name="admin_issue_floatip"),
]
