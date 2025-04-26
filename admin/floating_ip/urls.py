from django.urls import re_path

from .views import AdminFloatIPDataView, AdminFloatIPIndexView, AdminFloatIPResetEventAction

urlpatterns = [
    re_path(r"$", AdminFloatIPIndexView.as_view(), name="admin_floating_ip_index"),
    re_path(r"^(?P<pk>\d+)/$", AdminFloatIPDataView.as_view(), name="admin_floating_ip_data"),
    re_path(
        r"^(?P<pk>\d+)/reset_event/$", AdminFloatIPResetEventAction.as_view(), name="admin_floating_ip_reset_event"
    ),
]
