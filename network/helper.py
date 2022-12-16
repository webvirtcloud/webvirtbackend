from random import shuffle
from ipaddress import IPv4Network

from .models import Network, IPAddress


# First address is gateway, last address is broadcast
FIRST_IP_START = 2
LAST_IP_END = -1

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
    list_ips = list(net)[FIRST_IP_START:LAST_IP_END]
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
        list_ips = list(net)[FIRST_IP_START:LAST_IP_END]
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
        list_ips = list(net)[FIRST_IP_START:LAST_IP_END]
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
