from django.urls import re_path
from .views import AdminAccountProfileView, AdminAccountChangePasswordView


urlpatterns = [
    re_path("profile/?$", AdminAccountProfileView.as_view(), name="admin_profile"),
    re_path("change_password/?$", AdminAccountChangePasswordView.as_view(), name="admin_change_password"),
]
