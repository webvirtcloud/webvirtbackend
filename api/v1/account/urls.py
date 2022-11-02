from django.urls import include, re_path

from account.views import ProfileAPI

urlpatterns = [
    re_path(r"profile/?$", ProfileAPI.as_view(), name="profile_api"),
]
