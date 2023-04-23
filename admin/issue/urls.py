from django.urls import re_path
from .views import AdminIssueIndexView


urlpatterns = [
    re_path("$", AdminIssueIndexView.as_view(), name="admin_issue_index"),
]
