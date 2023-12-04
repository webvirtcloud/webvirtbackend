from django.urls import re_path
from .views import AdminFirewallIndexView

urlpatterns = [
    re_path(r"$", AdminFirewallIndexView.as_view(), name="admin_firewall_index"),
]
