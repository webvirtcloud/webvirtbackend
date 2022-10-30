from IPy import IP
from xml.etree import ElementTree

from .connection import wvmConnect
from .util import get_xml_data, randomMAC


def create_ipv4_subnet(subnet):
    """
    Func return IP address and netmask.
    """
    network = []
    net = IP(subnet)
    subnet = net[2 - len(network) : -1]

    for ip in subnet:
        network.append([ip.strNormal(), net.strNetmask()])
    return network


def network_size(net, dhcp=None):
    """
    Func return gateway, mask and dhcp pool.
    """
    mask = IP(net).strNetmask()
    addr = IP(net)
    gateway = addr[1].strNormal()
    dhcp_pool = [addr[2].strNormal(), addr[addr.len() - 2].strNormal()]
    if dhcp:
        return gateway, mask, dhcp_pool
    else:
        return gateway, mask, None


class wvmNetworks(wvmConnect):
    def get_networks_info(self):
        networks = []
        get_networks = self.get_networks()
        for network in get_networks:
            net = self.get_network(network)
            net_status = net.isActive()
            net_bridge = net.bridgeName()
            net_forwd = get_xml_data(net.XMLDesc(0), 'forward', 'mode')
            networks.append(
                {
                    'name': network,
                    'status': net_status,
                    'device': net_bridge,
                    'forward': net_forwd,
                }
            )
        return networks

    def define_network(self, xml):
        self.wvm.networkDefineXML(xml)

    def create_network(self, name, forward, gateway, mask, dhcp, bridge, openvswitch, fixed=False):
        xml = f"""
            <network>
                <name>{name}</name>"""
        if forward in ['nat', 'route', 'bridge']:
            xml += f"""<forward mode='{forward}'/>"""
        xml += """<bridge """
        if forward in ['nat', 'route', 'none']:
            xml += """stp='on' delay='0'"""
        if forward == 'bridge':
            xml += f"""name='{bridge}'"""
        xml += """/>"""
        if openvswitch is True:
            xml += """<virtualport type='openvswitch'/>"""
        if forward != 'bridge':
            xml += f"""
                        <ip address='{gateway}' netmask='{mask}'>"""
            if dhcp:
                xml += f"""<dhcp>
                            <range start='{dhcp[0]}' end='{dhcp[1]}' />"""
                if fixed:
                    fist_oct = int(dhcp[0].strip().split('.')[3])
                    last_oct = int(dhcp[1].strip().split('.')[3])
                    for ip in range(fist_oct, last_oct + 1):
                        xml += f"""<host mac='{randomMAC()}' ip='{gateway[:-2]}.{ip}' />"""
                xml += """</dhcp>"""

            xml += """</ip>"""
        xml += """</network>"""
        self.define_network(xml)
        net = self.get_network(name)
        net.create()
        net.setAutostart(1)


class wvmNetwork(wvmConnect):
    def __init__(self, host, login, passwd, conn, net):
        wvmConnect.__init__(self, host, login, passwd, conn)
        self.net = self.get_network(net)

    def get_name(self):
        return self.net.name()

    def XMLDesc(self, flags):
        return self.net.XMLDesc(flags)

    def define(self, xml):
        self.wvm.networkDefineXML(xml)

    def get_autostart(self):
        return self.net.autostart()

    def set_autostart(self, value):
        self.net.setAutostart(value)

    def is_active(self):
        return self.net.isActive()

    def get_uuid(self):
        return self.net.UUIDString()

    def get_bridge_device(self):
        try:
            return self.net.bridgeName()
        except Exception:
            return None

    def start(self):
        self.net.create()

    def stop(self):
        self.net.destroy()

    def delete(self):
        self.net.undefine()

    def get_ipv4_network(self):
        xml = self.XMLDesc(0)
        if not get_xml_data(xml, 'ip'):
            return None

        addrStr = get_xml_data(xml, 'ip', 'address')
        netmaskStr = get_xml_data(xml, 'ip', 'netmask')
        prefix = get_xml_data(xml, 'ip', 'prefix')

        if prefix:
            prefix = int(prefix)
            binstr = (prefix * "1") + ((32 - prefix) * "0")
            netmaskStr = str(IP(int(binstr, base=2)))

        if netmaskStr:
            netmask = IP(netmaskStr)
            gateway = IP(addrStr)
            network = IP(gateway.int() & netmask.int())
            ret = IP(f'{network}/{netmaskStr}')
        else:
            ret = IP(str(addrStr))

        return ret

    def get_ipv4_forward(self):
        xml = self.XMLDesc(0)
        fw = get_xml_data(xml, 'forward', 'mode')
        forwardDev = get_xml_data(xml, 'forward', 'dev')
        return [fw, forwardDev]

    def get_ipv4_dhcp_range(self):
        xml = self.XMLDesc(0)
        dhcpstart = get_xml_data(xml, 'ip/dhcp/range[1]', 'start')
        dhcpend = get_xml_data(xml, 'ip/dhcp/range[1]', 'end')
        if not dhcpstart and not dhcpend:
            return None
        return [IP(dhcpstart), IP(dhcpend)]

    def get_ipv4_dhcp_range_start(self):
        dhcp = self.get_ipv4_dhcp_range()
        if not dhcp:
            return None
        return dhcp[0]

    def get_ipv4_dhcp_range_end(self):
        dhcp = self.get_ipv4_dhcp_range()
        if not dhcp:
            return None
        return dhcp[1]

    def can_pxe(self):
        xml = self.XMLDesc(0)
        forward = self.get_ipv4_forward()[0]
        if forward and forward != "nat":
            return True
        return bool(get_xml_data(xml, 'ip/dhcp/bootp', 'file'))

    def get_mac_ipaddr(self):
        fixed_mac = []
        xml = self.XMLDesc(0)
        tree = ElementTree.fromstring(xml)
        dhcp_list = tree.findall('ip/dhcp/host')
        for i in dhcp_list:
            fixed_mac.append({'host': i.get('ip'), 'mac': i.get('mac')})

        return fixed_mac
