from django.urls import re_path

from floating_ip.views import FloatingIPListAPI

urlpatterns = [
    re_path(r"$", FloatingIPListAPI.as_view(), name="floating_ip_list_api"),
]
