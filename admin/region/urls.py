from django.urls import re_path
from .views import AdminRegionIndexView


urlpatterns = [
    re_path("$", AdminRegionIndexView.as_view(), name="admin_region_index"),
]
