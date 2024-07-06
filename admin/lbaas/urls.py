from django.urls import re_path
from .views import AdminLBaaSIndexView, AdminLBaaSDataView, AdminLBaaSResetEventAction

urlpatterns = [
    re_path(r"$", AdminLBaaSIndexView.as_view(), name="admin_lbaas_index"),
    re_path(r"^(?P<pk>\d+)/$", AdminLBaaSDataView.as_view(), name="admin_lbaas_data"),
    re_path(r"^(?P<pk>\d+)/reset_event/$", AdminLBaaSResetEventAction.as_view(), name="admin_lbaas_reset_event"),
]
