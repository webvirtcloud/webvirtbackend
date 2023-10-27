from django.urls import re_path

from floating_ip.views import FloatingIPListAPI, FloatingIPDataAPI

urlpatterns = [
    re_path(r"$", FloatingIPListAPI.as_view(), name="floating_ip_list_api"),
    re_path(r"(?P<ip>[0-9.]+)/?$", FloatingIPDataAPI.as_view(), name="floating_ip_data_api"),
]
