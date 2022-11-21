from django.urls import include, path, re_path

urlpatterns = [
    re_path(r"account/?", include("api.v1.account.urls")),
    re_path(r"projects/?", include("api.v1.project.urls")),
    re_path(r"sizes/?", include("api.v1.size.urls")),
    re_path(r"images/?", include("api.v1.image.urls")),
    re_path(r"regions/?", include("api.v1.region.urls")),
]
