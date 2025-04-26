from django.urls import re_path

from .views import AdminAccountChangePasswordView, AdminAccountProfileView

urlpatterns = [
    re_path(r"profile/?$", AdminAccountProfileView.as_view(), name="admin_profile"),
    re_path(r"change_password/?$", AdminAccountChangePasswordView.as_view(), name="admin_change_password"),
]
