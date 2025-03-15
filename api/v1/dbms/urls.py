from django.urls import re_path

from size.views import DBMSListAPI

urlpatterns = [
    re_path(r"$", DBMSListAPI.as_view(), name="dbms_list_api"),
]
