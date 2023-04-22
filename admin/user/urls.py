from django.urls import re_path
from .views import AdminUserIndexView


urlpatterns = [
    re_path("$", AdminUserIndexView.as_view(), name="admin_user_index"),
]
