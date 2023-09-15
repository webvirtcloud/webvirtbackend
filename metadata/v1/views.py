from django.conf import settings
from django.http import HttpResponse, JsonResponse

from network.models import Network, IPAddress
from keypair.models import KeyPairVirtance
from .utils import MetadataMixin


class MetadataV1Json(MetadataMixin):
    def get(self, request, *args, **kwargs):
        vendor_data = ""
        nameservers = []
        public_keys = []

        if self.virtance is None:
            return HttpResponse("Not Found", status=404)

        for i in KeyPairVirtance.objects.filter(virtance=self.virtance):
            public_keys.append(i.keypair.public_key)

        ipaddr = IPAddress.objects.filter(virtance=self.virtance)
        interfaces = {
            "public": [
                {
                    "compute_ipv4": {
                        "ip_address": ipaddr.filter(network__type=Network.COMPUTE).first().address,
                        "netmask": ipaddr.filter(network__type=Network.COMPUTE).first().network.netmask,
                        "gateway": ipaddr.filter(network__type=Network.COMPUTE).first().network.gateway,
                    },
                    "ipv4": {
                        "ip_address": ipaddr.filter(network__type=Network.PUBLIC).first().address,
                        "netmask": ipaddr.filter(network__type=Network.PUBLIC).first().network.netmask,
                        "gateway": ipaddr.filter(network__type=Network.PUBLIC).first().network.gateway,
                    },
                    "mac": "00:00:00:00:00:00",
                    "type": "public",
                }
            ],
            "private": [
                {
                    "ipv4": {
                        "ip_address": ipaddr.filter(network__type=Network.PRIVATE).first().address,
                        "netmask": ipaddr.filter(network__type=Network.PRIVATE).first().network.netmask,
                        "gateway": ipaddr.filter(network__type=Network.PRIVATE).first().network.gateway,
                    },
                    "mac": "00:00:00:00:00:00",
                    "type": "private",
                }
            ],
        }

        nameservers = [
            ipaddr.filter(network__type=Network.PUBLIC).first().network.dns1,
            ipaddr.filter(network__type=Network.PUBLIC).first().network.dns2,
        ]

        response = {
            "id": self.virtance.id,
            "hostname": self.virtance.name,
            "user-data": self.virtance.user_data,
            "vendor-data": vendor_data,
            "public-keys": public_keys,
            "region": self.virtance.region.slug,
            "interfaces": interfaces,
            "dns": {
                "nameservers": nameservers,
            },
        }
        return JsonResponse(response)


class MetadataIndex(MetadataMixin):
    def get(self, request, *args, **kwargs):
        if self.virtance is None:
            return HttpResponse("Not Found", status=404)
        data = ["id", "hostname", "user-data", "vendor-data", "public-keys", "region", "interfaces/", "dns/"]
        response = "\n".join(data)
        return HttpResponse(response)


class MetadataID(MetadataMixin):
    def get(self, request, *args, **kwargs):
        if self.virtance is None:
            return HttpResponse("Not Found", status=404)
        return HttpResponse(self.virtance.id)


class MetadataHostname(MetadataMixin):
    def get(self, request, *args, **kwargs):
        if self.virtance is None:
            return HttpResponse("Not Found", status=404)
        return HttpResponse(self.virtance.name)


class MetadataUserData(MetadataMixin):
    def get(self, request, *args, **kwargs):
        if self.virtance is None:
            return HttpResponse("Not Found", status=404)
        user_data = self.virtance.user_data if self.virtance.user_data else ""
        return HttpResponse(user_data)


class MetadataVendorData(MetadataMixin):
    def get(self, request, *args, **kwargs):
        if self.virtance is None:
            return HttpResponse("Not Found", status=404)
        vendor_data = ""
        return HttpResponse(vendor_data)


class MetadataPublicKeys(MetadataMixin):
    def get(self, request, *args, **kwargs):
        public_Keys = ""
        if self.virtance is None:
            return HttpResponse("Not Found", status=404)
        for i in KeyPairVirtance.objects.filter(virtance=self.virtance):
            if public_Keys:
                public_Keys += "\n"
            public_Keys += i.keypair.public_key
        return HttpResponse(public_Keys)


class MetadataInterfaces(MetadataMixin):
    def get(self, request, *args, **kwargs):
        if self.virtance is None:
            return HttpResponse("Not Found", status=404)
        data = ["public/", "private/"]
        response = "\n".join(data)
        return HttpResponse(response)


class MetadataInterfacesPublic(MetadataMixin):
    def get(self, request, *args, **kwargs):
        if self.virtance is None:
            return HttpResponse("Not Found", status=404)
        data = ["0/"]
        response = "\n".join(data)
        return HttpResponse(response)


class MetadataInterfacesPublic(MetadataMixin):
    def get(self, request, *args, **kwargs):
        if self.virtance is None:
            return HttpResponse("Not Found", status=404)
        data = ["mac", "type", "compute_ipv4/", "ipv4/"]
        response = "\n".join(data)
        return HttpResponse(response)


class MetadataInterfacesPublicMAC(MetadataMixin):
    def get(self, request, *args, **kwargs):
        if self.virtance is None:
            return HttpResponse("Not Found", status=404)
        mac = "00:00:00:00:00:00"
        return HttpResponse(mac)


class MetadataInterfacesPublicType(MetadataMixin):
    def get(self, request, *args, **kwargs):
        if self.virtance is None:
            return HttpResponse("Not Found", status=404)
        return HttpResponse("public")


class MetadataInterfacesPublicIPv4(MetadataMixin):
    def get(self, request, *args, **kwargs):
        if self.virtance is None:
            return HttpResponse("Not Found", status=404)
        data = ["address", "netmask", "gateway"]
        response = "\n".join(data)
        return HttpResponse(response)


class MetadataInterfacesPublicIPv4Address(MetadataMixin):
    def get(self, request, *args, **kwargs):
        ipaddr = IPAddress.objects.filter(virtance=self.virtance, network__type=Network.PUBLIC).first()
        if self.virtance is None or ipaddr is None:
            return HttpResponse("Not Found", status=404)
        return HttpResponse(ipaddr.address)


class MetadataInterfacesPublicIPv4Netmask(MetadataMixin):
    def get(self, request, *args, **kwargs):
        ipaddr = IPAddress.objects.filter(virtance=self.virtance, network__type=Network.PUBLIC).first()
        if self.virtance is None or ipaddr is None:
            return HttpResponse("Not Found", status=404)
        return HttpResponse(ipaddr.network.netmask)


class MetadataInterfacesPublicIPv4Gateway(MetadataMixin):
    def get(self, request, *args, **kwargs):
        ipaddr = IPAddress.objects.filter(virtance=self.virtance, network__type=Network.PUBLIC).first()
        if self.virtance is None or ipaddr is None:
            return HttpResponse("Not Found", status=404)
        return HttpResponse(ipaddr.network.gateway)


class MetadataInterfacesPublicComputeIPv4(MetadataMixin):
    def get(self, request, *args, **kwargs):
        if self.virtance is None:
            return HttpResponse("Not Found", status=404)
        data = ["address", "netmask", "gateway"]
        response = "\n".join(data)
        return HttpResponse(response)


class MetadataInterfacesPublicComputeIPv4Address(MetadataMixin):
    def get(self, request, *args, **kwargs):
        ipaddr = IPAddress.objects.filter(virtance=self.virtance, network__type=Network.COMPUTE).first()
        if self.virtance is None or ipaddr is None:
            return HttpResponse("Not Found", status=404)
        return HttpResponse(ipaddr.address)


class MetadataInterfacesPublicComputeIPv4Netmask(MetadataMixin):
    def get(self, request, *args, **kwargs):
        ipaddr = IPAddress.objects.filter(virtance=self.virtance, network__type=Network.COMPUTE).first()
        if self.virtance is None or ipaddr is None:
            return HttpResponse("Not Found", status=404)
        return HttpResponse(ipaddr.network.netmask)


class MetadataInterfacesPublicComputeIPv4Gateway(MetadataMixin):
    def get(self, request, *args, **kwargs):
        ipaddr = IPAddress.objects.filter(virtance=self.virtance, network__type=Network.COMPUTE).first()
        if self.virtance is None or ipaddr is None:
            return HttpResponse("Not Found", status=404)
        return HttpResponse(ipaddr.network.gateway)


class MetadataInterfacesPrivate(MetadataMixin):
    def get(self, request, *args, **kwargs):
        if self.virtance is None:
            return HttpResponse("Not Found", status=404)
        data = ["0/"]
        response = "\n".join(data)
        return HttpResponse(response)


class MetadataInterfacesPrivate(MetadataMixin):
    def get(self, request, *args, **kwargs):
        if self.virtance is None:
            return HttpResponse("Not Found", status=404)
        data = ["mac", "type", "ipv4/"]
        response = "\n".join(data)
        return HttpResponse(response)


class MetadataInterfacesPrivateMAC(MetadataMixin):
    def get(self, request, *args, **kwargs):
        if self.virtance is None:
            return HttpResponse("Not Found", status=404)
        mac = "00:00:00:00:00:00"
        return HttpResponse(mac)


class MetadataInterfacesPrivateType(MetadataMixin):
    def get(self, request, *args, **kwargs):
        if self.virtance is None:
            return HttpResponse("Not Found", status=404)
        return HttpResponse("private")


class MetadataInterfacesPrivateIPv4(MetadataMixin):
    def get(self, request, *args, **kwargs):
        if self.virtance is None:
            return HttpResponse("Not Found", status=404)
        data = ["address", "netmask", "gateway"]
        response = "\n".join(data)
        return HttpResponse(response)


class MetadataInterfacesPrivateIPv4Address(MetadataMixin):
    def get(self, request, *args, **kwargs):
        ipaddr = IPAddress.objects.filter(virtance=self.virtance, network__type=Network.PRIVATE).first()
        if self.virtance is None or ipaddr is None:
            return HttpResponse("Not Found", status=404)
        return HttpResponse(ipaddr.address)


class MetadataInterfacesPrivateIPv4Netmask(MetadataMixin):
    def get(self, request, *args, **kwargs):
        ipaddr = IPAddress.objects.filter(virtance=self.virtance, network__type=Network.PRIVATE).first()
        if self.virtance is None or ipaddr is None:
            return HttpResponse("Not Found", status=404)
        return HttpResponse(ipaddr.network.netmask)


class MetadataInterfacesPrivateIPv4Gateway(MetadataMixin):
    def get(self, request, *args, **kwargs):
        ipaddr = IPAddress.objects.filter(virtance=self.virtance, network__type=Network.PRIVATE).first()
        if self.virtance is None or ipaddr is None:
            return HttpResponse("Not Found", status=404)
        return HttpResponse(ipaddr.network.gateway)


class MetadataDNS(MetadataMixin):
    def get(self, request, *args, **kwargs):
        if self.virtance is None:
            return HttpResponse("Not Found", status=404)
        data = ["nameservers"]
        response = "\n".join(data)
        return HttpResponse(response)


class MetadataDNSNameservers(MetadataMixin):
    def get(self, request, *args, **kwargs):
        ipaddr = IPAddress.objects.filter(virtance=self.virtance, network__type=Network.PUBLIC).first()
        if self.virtance is None or ipaddr is None:
            return HttpResponse("Not Found", status=404)
        response = "\n".join([ipaddr.network.dns1, ipaddr.network.dns2])
        return HttpResponse(response)
