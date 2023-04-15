import random
from ipaddress import IPv4Network, IPv6Network, ip_address

from virtance.models import Virtance
from .models import Network, IPAddress


# First is a gateway and last address is broadcast
SUBNET_RANGE = slice(2, -1)


def assign_free_ipv4_compute(virtance_id):
    virtance = Virtance.objects.get(id=virtance_id)
    virtances = Virtance.objects.filter(compute=virtance.compute, is_deleted=False)
    network = Network.objects.get(
        region=virtance.region,
        version=Network.IPv4, 
        type=Network.COMPUTE, 
        is_active=True, 
        is_deleted=False
    )
    assigned_ipv4_compute = IPAddress.objects.filter(network=network, virtance__in=virtances)
    ipaddrs = list(IPv4Network(f"{network.cidr}/{network.netmask}"))[SUBNET_RANGE]
    for ipaddr in random.sample(ipaddrs, k=len(ipaddrs)):
        if str(ipaddr) not in [ip.address for ip in assigned_ipv4_compute]:
            IPAddress.objects.create(network=network, address=str(ipaddr), virtance=virtance)
            return True
    return False


def assign_free_ipv4_public(virtance_id):
    virtance = Virtance.objects.get(id=virtance_id)
    networks = Network.objects.filter(
        region=virtance.region, 
        version=Network.IPv4, 
        type=Network.PUBLIC, 
        is_active=True, 
        is_deleted=False
    )
    for net in networks:
        ipaddrs = list(IPv4Network(f"{net.cidr}/{net.netmask}"))[SUBNET_RANGE]
        for ipaddr in random.sample(ipaddrs, k=len(ipaddrs)):
            if not IPAddress.objects.filter(network=net, address=str(ipaddr)).exists():
                IPAddress.objects.create(network=net, address=str(ipaddr), virtance=virtance)
                return True
    return False


def assign_free_ipv4_private(virtance_id):
    virtance = Virtance.objects.get(id=virtance_id)
    networks = Network.objects.filter(
        region=virtance.region,
        version=Network.IPv4, 
        type=Network.PRIVATE, 
        is_active=True, 
        is_deleted=False
    )
    for net in networks:
        ipaddrs = list(IPv4Network(f"{net.cidr}/{net.netmask}"))[SUBNET_RANGE]
        for ipaddr in random.sample(ipaddrs, k=len(ipaddrs)):
            if not IPAddress.objects.filter(network=net, address=str(ipaddr)).exists():
                IPAddress.objects.create(network=net, address=str(ipaddr), virtance=virtance)
                return True
    return False


def assign_free_ipv6_public(virtance_id):
    virtance = Virtance.objects.get(id=virtance_id)
    networks = Network.objects.filter(
        region=virtance.region,
        version=Network.IPv6, 
        type=Network.PUBLIC,
        is_active=True, 
        is_deleted=False
    )
    for net in networks:
        subnet = IPv6Network(f"{net.cidr}/{net.netmask}")
        step = 16
        limit = 2 ** step
        start = int(subnet.network_address) + step
        end = int(subnet.broadcast_address) + 1
        for i in random.sample(range(start, end, step), k=limit):
            if not IPAddress.objects.filter(network=net, address=str(ip_address(i))).exists():
                IPAddress.objects.create(network=net, address=str(ip_address(i)), virtance=virtance)
                return True
    return False
