from django.urls import re_path
from .views import AdminDBMSIndexView, AdminDBMSCreateView, AdminDBMSUpdateView, AdminDBMSDeleteView


urlpatterns = [
    re_path(r"$", AdminDBMSIndexView.as_view(), name="admin_dbms_index"),
    re_path(r"create/?$", AdminDBMSCreateView.as_view(), name="admin_dbms_create"),
    re_path(r"update/(?P<pk>\d+)/?$", AdminDBMSUpdateView.as_view(), name="admin_dbms_update"),
    re_path(r"delete/(?P<pk>\d+)/?$", AdminDBMSDeleteView.as_view(), name="admin_dbms_delete"),
]
