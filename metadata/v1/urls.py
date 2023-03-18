from django.urls import re_path

from .views import MetadataIndex, MetadataID, MetadataHostname, MetadataUserData, MetadataVendorData
from .views import MetadataPublicKeys, MetadataInterfaces, MetadataInterfacesPublic, MetadataInterfacesPublicMAC
from .views import MetadataInterfacesPublicType, MetadataInterfacesPublicIPv4, MetadataInterfacesPublicIPv4Address
from .views import MetadataInterfacesPublicIPv4Netmask, MetadataInterfacesPublicIPv4Gateway
from .views import MetadataInterfacesPublicComputeIPv4, MetadataInterfacesPublicComputeIPv4Address
from .views import MetadataInterfacesPublicComputeIPv4Netmask, MetadataInterfacesPublicComputeIPv4Gateway
from .views import MetadataInterfacesPrivate, MetadataInterfacesPrivateMAC, MetadataInterfacesPrivateType
from .views import MetadataInterfacesPrivateIPv4, MetadataInterfacesPrivateIPv4Address
from .views import MetadataInterfacesPrivateIPv4Netmask, MetadataInterfacesPrivateIPv4Gateway
from .views import MetadataDNS, MetadataDNSNameservers


urlpatterns = [
    re_path(r"$", MetadataIndex.as_view(), name="metadata_v1_index"),
    re_path(r"id$", MetadataID.as_view(), name="metadata_v1_id"),
    re_path(r"hostname$", MetadataHostname.as_view(), name="metadata_v1_hostname"),
    re_path(r"user-data$", MetadataUserData.as_view(), name="metadata_v1_user_data"),
    re_path(r"vendor-data$", MetadataVendorData.as_view(), name="metadata_v1_vendor_data"),
    re_path(r"public-keys$", MetadataPublicKeys.as_view(), name="metadata_v1_public_keys"),
    re_path(r"public-keys$", MetadataPublicKeys.as_view(), name="metadata_v1_public_keys"),
    re_path(r"interfaces/$", MetadataInterfaces.as_view(), name="metadata_v1_interfaces"),
    re_path(
        r"interfaces/public/$", 
        MetadataInterfacesPublic.as_view(), name="metadata_v1_interfaces_public"
    ),
    re_path(
        r"interfaces/public/mac$", 
        MetadataInterfacesPublicMAC.as_view(), name="metadata_v1_interfaces_public_mac"
    ),
    re_path(
        r"interfaces/public/type$", 
        MetadataInterfacesPublicType.as_view(), name="metadata_v1_interfaces_public_type"
    ),
    re_path(
        r"interfaces/public/ipv4/$", 
        MetadataInterfacesPublicIPv4.as_view(), name="metadata_v1_interfaces_public_ipv4"
    ),
    re_path(
        r"interfaces/public/ipv4/address$", 
        MetadataInterfacesPublicIPv4Address.as_view(), name="metadata_v1_interfaces_public_ipv4_address"
    ),
    re_path(
        r"interfaces/public/ipv4/netmask$", 
        MetadataInterfacesPublicIPv4Netmask.as_view(), name="metadata_v1_interfaces_public_ipv4_netmask"
    ),
    re_path(
        r"interfaces/public/ipv4/gateway$", 
        MetadataInterfacesPublicIPv4Gateway.as_view(), name="metadata_v1_interfaces_public_ipv4_gateway"
    ),
        re_path(
        r"interfaces/public/compute_ipv4/$", 
        MetadataInterfacesPublicComputeIPv4.as_view(), name="metadata_v1_interfaces_public_compute_ipv4"
    ),
    re_path(
        r"interfaces/public/compute_ipv4/address$", 
        MetadataInterfacesPublicComputeIPv4Address.as_view(), name="metadata_v1_interfaces_public_compute_ipv4_address"
    ),
    re_path(
        r"interfaces/public/compute_ipv4/netmask$", 
        MetadataInterfacesPublicComputeIPv4Netmask.as_view(), name="metadata_v1_interfaces_public_compute_ipv4_netmask"
    ),
    re_path(
        r"interfaces/public/compute_ipv4/gateway$", 
        MetadataInterfacesPublicComputeIPv4Gateway.as_view(), name="metadata_v1_interfaces_public_compute_ipv4_gateway"
    ),
    re_path(
        r"interfaces/private/$", 
        MetadataInterfacesPrivate.as_view(), name="metadata_v1_interfaces_private"
    ),
    re_path(
        r"interfaces/private/mac$", 
        MetadataInterfacesPrivateMAC.as_view(), name="metadata_v1_interfaces_private_mac"
    ),
    re_path(
        r"interfaces/private/type$", 
        MetadataInterfacesPrivateType.as_view(), name="metadata_v1_interfaces_private_type"
    ),
    re_path(
        r"interfaces/private/ipv4/$", 
        MetadataInterfacesPrivateIPv4.as_view(), name="metadata_v1_interfaces_private_ipv4"
    ),
    re_path(
        r"interfaces/private/ipv4/address$", 
        MetadataInterfacesPrivateIPv4Address.as_view(), name="metadata_v1_interfaces_private_ipv4_address"
    ),
    re_path(
        r"interfaces/private/ipv4/netmask$", 
        MetadataInterfacesPrivateIPv4Netmask.as_view(), name="metadata_v1_interfaces_private_ipv4_netmask"
    ),
    re_path(
        r"interfaces/private/ipv4/gateway$", 
        MetadataInterfacesPrivateIPv4Gateway.as_view(), name="metadata_v1_interfaces_private_ipv4_gateway"
    ),
    re_path(
        r"dns/$", MetadataDNS.as_view(), name="metadata_v1_dns"
    ),
    re_path(
        r"dns/nameservers$", MetadataDNSNameservers.as_view(), name="metadata_v1_dns_mameservers"
    ),
]
