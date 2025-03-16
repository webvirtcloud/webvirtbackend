from django.urls import include, re_path
from .views import AdminIndexView, AdminSingInView, AdminSingOutView


urlpatterns = [
    re_path(r"^$", AdminIndexView.as_view(), name="admin_index"),
    re_path(r"sign_in/?$", AdminSingInView.as_view(), name="admin_sign_in"),
    re_path(r"sign_out/?$", AdminSingOutView.as_view(), name="admin_sign_out"),
    re_path(r"user/", include("admin.user.urls")),
    re_path(r"account/", include("admin.account.urls")),
    re_path(r"region/", include("admin.region.urls")),
    re_path(r"dbms/", include("admin.dbms.urls")),
    re_path(r"size/", include("admin.size.urls")),
    re_path(r"template/", include("admin.template.urls")),
    re_path(r"image/", include("admin.image.urls")),
    re_path(r"lbaas/", include("admin.lbaas.urls")),
    re_path(r"network/", include("admin.network.urls")),
    re_path(r"compute/", include("admin.compute.urls")),
    re_path(r"virtance/", include("admin.virtance.urls")),
    re_path(r"firewall/", include("admin.firewall.urls")),
    re_path(r"floating_ip/", include("admin.floating_ip.urls")),
    re_path(r"issue/", include("admin.issue.urls")),
]
