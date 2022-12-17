import requests
from django.conf import settings
from webvirtcloud.celery import app

from compute.helper import assign_free_compute, WebVirtCompute
from network.helper import (
    assign_free_ipv4_public,
    assign_free_ipv4_compute,
    assign_free_ipv4_private,
)
from compute.models import Compute
from network.models import Network, IPAddress
from .models import Virtance


@app.task
def create_virtance(virtance_id, password):
    compute = None
    ipv4_public = None
    ipv4_compute = None
    ipv4_private = None
    virtance = Virtance.objects.get(id=virtance_id)

    if assign_free_compute(virtance.id) is True:
        compute = Compute.objects.get(id=virtance.compute.id)

    if assign_free_ipv4_compute(virtance.id) is True:
        ipv4_compute = IPAddress.objects.get(network__type=Network.COMPUTE, virtance=virtance)

    if assign_free_ipv4_public(virtance.id) is True:
        ipv4_public = IPAddress.objects.get(network__type=Network.PUBLIC, virtance=virtance)

    if assign_free_ipv4_private(virtance.id) is True:
        ipv4_private = IPAddress.objects.get(network__type=Network.PRIVATE, virtance=virtance)

    if compute and ipv4_public and ipv4_compute and ipv4_private:
        images = [
            {
                "name": virtance.name,
                "size": virtance.size.disk,
                "url": settings.IMAGE_URL + "/" + virtance.image.slug + ".qcow2",
                "md5sum": virtance.image.md5sum,
                "primary": True
            }
        ]
        network = [
            {
                "v4": {
                    "public": {
                        "primary": {
                            "address": ipv4_public.address,
                            "gateway": ipv4_public.network.gateway,
                            "netmask": ipv4_public.network.netmask,
                            "dns1": ipv4_public.network.dns1,
                            "dns2": ipv4_public.network.dns2
                            
                        },
                        "secondary": {
                            "address": ipv4_compute.address,
                            "gateway": ipv4_compute.network.gateway,
                            "netmask": ipv4_compute.network.netmask
                        }
                    },
                    "private": {
                        "primary": {
                            "address": ipv4_private.address,
                            "gateway": ipv4_private.network.gateway,
                            "netmask": ipv4_private.network.netmask
                            
                        },
                        "secondary": {
                            "address": "",
                            "gateway": "",
                            "netmask": ""
                        }
                    }
                },
                "v6": {
                    "public": {
                        "primary": {
                            "address": "",
                            "gateway": "",
                            "prefix": "",
                            "dns1": "",
                            "dns2": ""
                            
                        }
                    }
                }
            }
        ]
        keypairs = []
        wvcomp = WebVirtCompute(compute.token, compute.hostname)
        wvcomp.create_virtance(
            virtance.size.vcpu,
            virtance.size.memory,
            images, 
            network, 
            keypairs, 
            root_password
        )
