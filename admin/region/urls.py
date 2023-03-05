from django.urls import re_path
from .views import AdminRegionIndexView, AdminRegionCreateView


urlpatterns = [
    re_path("$", AdminRegionIndexView.as_view(), name="admin_region_index"),
    re_path("create/?$", AdminRegionCreateView.as_view(), name="admin_region_create"),
]
