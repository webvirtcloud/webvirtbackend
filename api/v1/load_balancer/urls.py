from django.urls import re_path

from lbaas.views import LBaaSDataAPI, LBaaSForwardRulesAPI, LBaaSListAPI, LBaaSVirtancesAPI

urlpatterns = [
    re_path(r"$", LBaaSListAPI.as_view(), name="lbaas_list_api"),
    re_path(r"(?P<uuid>[0-9a-f-]+)/?$", LBaaSDataAPI.as_view(), name="lbaas_data_api"),
    re_path(r"(?P<uuid>[0-9a-f-]+)/virtances/?$", LBaaSVirtancesAPI.as_view(), name="lbaas_virtance_api"),
    re_path(
        r"(?P<uuid>[0-9a-f-]+)/forwarding_rules/?$", LBaaSForwardRulesAPI.as_view(), name="lbaas_forward_rules_api"
    ),
]
