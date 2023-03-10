from django.urls import re_path
from .views import AdminComputeIndexView, AdminComputeCreateView, AdminComputeUpdateView, AdminComputeDeleteView
from .views import AdminComputeOverviewView, AdminComputeStoragesView


urlpatterns = [
    re_path("$", AdminComputeIndexView.as_view(), name="admin_compute_index"),
    re_path("create/?$", AdminComputeCreateView.as_view(), name="admin_compute_create"),
    re_path("update/(?P<pk>\d+)/?$", AdminComputeUpdateView.as_view(), name="admin_compute_update"),
    re_path("delete/(?P<pk>\d+)/?$", AdminComputeDeleteView.as_view(), name="admin_compute_delete"),

    re_path("overview/(?P<pk>\d+)/?$", AdminComputeOverviewView.as_view(), name="admin_compute_overview"),
    re_path("storages/(?P<pk>\d+)/?$", AdminComputeStoragesView.as_view(), name="admin_compute_storages"),
]
