from django.urls import re_path

from .views import (
    AdminNetworkCreateView,
    AdminNetworkDeleteView,
    AdminNetworkIndexView,
    AdminNetworkListView,
    AdminNetworkUpdateView,
)

urlpatterns = [
    re_path(r"$", AdminNetworkIndexView.as_view(), name="admin_network_index"),
    re_path(r"create/?$", AdminNetworkCreateView.as_view(), name="admin_network_create"),
    re_path(r"list/(?P<pk>\d+)/?$", AdminNetworkListView.as_view(), name="admin_network_list"),
    re_path(r"update/(?P<pk>\d+)/?$", AdminNetworkUpdateView.as_view(), name="admin_network_update"),
    re_path(r"delete/(?P<pk>\d+)/?$", AdminNetworkDeleteView.as_view(), name="admin_network_delete"),
]
