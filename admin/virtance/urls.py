from django.urls import re_path
from .views import AdminVirtanceIndexView, AdminVirtanceDataView


urlpatterns = [
    re_path("$", AdminVirtanceIndexView.as_view(), name="admin_virtance_index"),
    re_path(r"^(?P<pk>\d+)/$", AdminVirtanceDataView.as_view(), name="admin_virtance_data"),
]
