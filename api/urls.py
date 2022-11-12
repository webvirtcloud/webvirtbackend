from django.urls import include, path, re_path

urlpatterns = [
    re_path(r"account/?", include("api.v1.account.urls")),
    re_path(r"projects/?", include("api.v1.project.urls")),
]
