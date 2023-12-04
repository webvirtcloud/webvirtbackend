from django.urls import re_path
from .views import AdminUserIndexView, AdminUserDataView


urlpatterns = [
    re_path(r"$", AdminUserIndexView.as_view(), name="admin_user_index"),
    re_path(r"^(?P<pk>\d+)/$", AdminUserDataView.as_view(), name="admin_user_data"),
]
