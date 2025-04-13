from django.urls import re_path
from .views import AdminDBaaSIndexView, AdminDBaaSDataView

urlpatterns = [
    re_path(r"$", AdminDBaaSIndexView.as_view(), name="admin_dbaas_index"),
    re_path(r"^(?P<pk>\d+)/$", AdminDBaaSDataView.as_view(), name="admin_dbaas_data"),
]
