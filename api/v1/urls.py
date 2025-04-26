from django.urls import include, re_path

urlpatterns = [
    re_path(r"^account/?", include("api.v1.account.urls")),
    re_path(r"^billing/?", include("api.v1.billing.urls")),
    re_path(r"^projects/?", include("api.v1.project.urls")),
    re_path(r"^dbms/?", include("api.v1.dbms.urls")),
    re_path(r"^sizes/?", include("api.v1.size.urls")),
    re_path(r"^images/?", include("api.v1.image.urls")),
    re_path(r"^regions/?", include("api.v1.region.urls")),
    re_path(r"^keypairs/?", include("api.v1.keypair.urls")),
    re_path(r"^virtances/?", include("api.v1.virtance.urls")),
    re_path(r"^firewalls/?", include("api.v1.firewall.urls")),
    re_path(r"^databases/?", include("api.v1.database.urls")),
    re_path(r"^floating_ips/?", include("api.v1.floating_ip.urls")),
    re_path(r"^load_balancers/?", include("api.v1.load_balancer.urls")),
]
