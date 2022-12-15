from random import shuffle
from ipaddress import IPv4Network

from .models import Network, IPAddress


def assign_free_ipv4_compute(virtance_id):
    virtance = Virtance.objects.get(id=virtance_id)
    virtances = Virtance.objects.filter(compute=virtance.compute, is_deleted=False)
    network = Network.objects.get(
        region=virtance.region,
        ip_version=Network.IPv4, 
        type=Network.COMPUTE, 
        is_active=True, 
        is_deleted=False
    )
    assigned_ipv4_compute = IPAddress.objects.filter(network=network, virtance__in=virtances)
    # Use from 2nd to last IP address
    list_ips = list(net)[2:-1]
    shuffle(list_ips)
    for ip in list_ips:
        if str(ip) not in [ip.address for ip in assigned_ipv4_compute]:
            IPAddress.objects.create(
                network=network, address=str(ip), virtance=virtance, netmask=str(net.netmask)
            )
            return True
    return False


def assign_free_ipv4_public(region_id, virtance_id):
    virtance = Virtance.objects.get(id=virtance_id)
    networks = Network.objects.filter(
        region=virtance.region, 
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
                IPAddress.objects.create(
                    network=net, address=str(ip), virtance=virtance, netmask=str(net.netmask)
                )
                return True
    return False


def assign_free_ipv4_private(virtance_id):
    virtance = Virtance.objects.get(id=virtance_id)
    networks = Network.objects.filter(
        region=virtance.region,
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
                IPAddress.objects.create(
                    network=net, address=str(ip), virtance=virtance, netmask=str(net.netmask)
                )
                return True
    return False


def assign_free_ipv6_public(region_id, virtance_id):
    pass
