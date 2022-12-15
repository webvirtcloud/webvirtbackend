from random import shuffle
from ipaddress import IPv4Network

from .models import Network


def set_free_ipv4_public(region_id, virtance_id):
    networks = Network.objects.filter(
        region_id=region_id, 
        ip_version=Network.IPv4, 
        type=Network.PUBLIC, 
        is_active=True, 
        is_deleted=False
    )
    for net in networks:
        # Use from 2nd to last IP address
        list_ips = list(net)[2:-1]
        shuffle(list_ips)
        for ip in list_ips:
            if not IPAddress.objects.filter(network=net, address=str(ip)).exists():
                ipaddress = IPAddress.objects.create(
                    network=net, address=str(ip), virtance_id=virtance_id, netmask=str(net.netmask)
                )
                return ipaddress.id
    return None


def set_free_ipv4_compute(region_id, virtance_id):
    networks = Network.objects.filter(
        region_id=region_id, 
        ip_version=Network.IPv4, 
        type=Network.COMPUTE, 
        is_active=True, 
        is_deleted=False
    )
    for net in networks:
        # Use from 2nd to last IP address
        list_ips = list(net)[2:-1]
        shuffle(list_ips)
        for ip in list_ips:
            if not IPAddress.objects.filter(network=net, address=str(ip)).exists():
                ipaddress = IPAddress.objects.create(
                    network=net, address=str(ip), virtance_id=virtance_id, netmask=str(net.netmask)
                )
                return ipaddress.id
    return None


def set_free_ipv4_private(region_id, virtance_id):
    networks = Network.objects.filter(
        region_id=region_id, 
        ip_version=Network.IPv4, 
        type=Network.PRIVATE, 
        is_active=True, 
        is_deleted=False
    )
    for net in networks:
        # Use from 2nd to last IP address
        list_ips = list(net)[2:-1]
        shuffle(list_ips)
        for ip in list_ips:
            if not IPAddress.objects.filter(network=net, address=str(ip)).exists():
                ipaddress = IPAddress.objects.create(
                    network=net, address=str(ip), virtance_id=virtance_id, netmask=str(net.netmask)
                )
                return ipaddress.id
    return None


def set_free_ipv6_public(region_id, virtance_id):
    pass
