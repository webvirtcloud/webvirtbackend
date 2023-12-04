from django.urls import re_path
from .views import AdminRegionIndexView, AdminRegionCreateView, AdminRegionUpdateView, AdminRegionDeleteView


urlpatterns = [
    re_path(r"$", AdminRegionIndexView.as_view(), name="admin_region_index"),
    re_path(r"create/?$", AdminRegionCreateView.as_view(), name="admin_region_create"),
    re_path(r"update/(?P<pk>\d+)/?$", AdminRegionUpdateView.as_view(), name="admin_region_update"),
    re_path(r"delete/(?P<pk>\d+)/?$", AdminRegionDeleteView.as_view(), name="admin_region_delete"),
]
