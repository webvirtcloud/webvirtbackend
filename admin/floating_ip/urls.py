from django.urls import re_path
from .views import AdminFloatIPIndexView

urlpatterns = [
    re_path(r"$", AdminFloatIPIndexView.as_view(), name="admin_floating_ip_index"),
]
