from libvirt import VIR_INTERFACE_XML_INACTIVE

from .connection import wvmConnect
from .util import get_xml_data


class wvmInterfaces(wvmConnect):
    def get_iface_info(self, name):
        iface = self.get_iface(name)
        xml = iface.XMLDesc(1)
        mac = iface.MACString()
        itype = get_xml_data(xml, element="type")
        state = iface.isActive()
        return {"name": name, "type": itype, "state": state, "mac": mac}

    def define_iface(self, xml, flag=0):
        self.wvm.interfaceDefineXML(xml, flag)

    def create_iface(
        self, name, itype, mode, netdev, ipv4_type, ipv4_addr, ipv4_gw, ipv6_type, ipv6_addr, ipv6_gw, stp, delay
    ):
        xml = f"""<interface type='{itype}' name='{name}'>
                    <start mode='{mode}'/>"""
        if ipv4_type == "dhcp":
            xml += """<protocol family='ipv4'>
                        <dhcp/>
                      </protocol>"""
        if ipv4_type == "static":
            address, prefix = ipv4_addr.split("/")
            xml += f"""<protocol family='ipv4'>
                        <ip address='{address}' prefix='{prefix}'/>
                        <route gateway='{ipv4_gw}'/>
                      </protocol>"""
        if ipv6_type == "dhcp":
            xml += """<protocol family='ipv6'>
                        <dhcp/>
                      </protocol>"""
        if ipv6_type == "static":
            address, prefix = ipv6_addr.split("/")
            xml += f"""<protocol family='ipv6'>
                        <ip address='{address}' prefix='{prefix}'/>
                        <route gateway='{ipv6_gw}'/>
                      </protocol>"""
        if itype == "bridge":
            xml += f"""<bridge stp='{stp}' delay='{delay}'>
                        <interface name='{netdev}' type='ethernet'/>
                      </bridge>"""
        xml += """</interface>"""
        self.define_iface(xml)
        iface = self.get_iface(name)
        iface.create()


class wvmInterface(wvmConnect):
    def __init__(self, host, login, passwd, conn, iface):
        wvmConnect.__init__(self, host, login, passwd, conn)
        self.iface = self.get_iface(iface)

    def _XMLDesc(self, flags=1):
        return self.iface.XMLDesc(flags)

    def get_start_mode(self):
        try:
            xml = self._XMLDesc(VIR_INTERFACE_XML_INACTIVE)
            return get_xml_data(xml, "start", "mode")
        except Exception:
            return None

    def is_active(self):
        return self.iface.isActive()

    def get_mac(self):
        mac = self.iface.MACString()
        if mac:
            return mac
        else:
            return None

    def get_type(self):
        xml = self._XMLDesc()
        return get_xml_data(xml, element="type")

    def get_ipv4_type(self):
        try:
            xml = self._XMLDesc(VIR_INTERFACE_XML_INACTIVE)
            ip_family = get_xml_data(xml, "protocol", "family")
            if ip_family == "ipv4":
                ipaddr = get_xml_data(xml, "protocol/ip", "address")
                if ipaddr:
                    return "static"
                else:
                    return "dhcp"
            return None
        except Exception:
            return None

    def get_ipv4(self):
        xml = self._XMLDesc()
        ip_family = get_xml_data(xml, "protocol", "family")
        if ip_family == "ipv4":
            int_ipv4_ip = get_xml_data(xml, "protocol/ip", "address")
            int_ipv4_mask = get_xml_data(xml, "protocol/ip", "prefix")
        else:
            int_ipv4_ip = None
            int_ipv4_mask = None
        if not int_ipv4_ip or not int_ipv4_mask:
            return None
        else:
            return f"{int_ipv4_ip}/{int_ipv4_mask}"

    def get_ipv6_type(self):
        try:
            xml = self._XMLDesc()
            ip_family = get_xml_data(xml, "protocol", "family")
            if ip_family == "ipv6":
                ipaddr = get_xml_data(xml, "protocol/ip", "address")
            else:
                ip_family = get_xml_data(xml, "protocol[2]", "family")
                if ip_family == "ipv6":
                    ipaddr = get_xml_data(xml, "protocol[2]/ip", "address")
                else:
                    return None
            if ipaddr:
                return "static"
            else:
                return "dhcp"
        except Exception:
            return None

    def get_ipv6(self):
        xml = self._XMLDesc()
        ip_family = get_xml_data(xml, "protocol", "family")
        if ip_family == "ipv6":
            int_ipv6_ip = get_xml_data(xml, "protocol/ip", "address")
            int_ipv6_mask = get_xml_data(xml, "protocol/ip", "prefix")
        else:
            ip_family = get_xml_data(xml, "protocol[2]", "family")
            if ip_family == "ipv6":
                int_ipv6_ip = get_xml_data(xml, "protocol[2]/ip", "address")
                int_ipv6_mask = get_xml_data(xml, "protocol[2]/ip", "prefix")
            else:
                return None
        if not int_ipv6_ip or not int_ipv6_mask:
            return None
        else:
            return f"{int_ipv6_ip}/{int_ipv6_mask}"

    def get_bridge(self):
        if self.get_type() == "bridge":
            xml = self._XMLDesc()
            return get_xml_data(xml, "bridge/interface", "name")
        else:
            return None

    def stop_iface(self):
        self.iface.destroy()

    def start_iface(self):
        self.iface.create()

    def delete_iface(self):
        self.iface.undefine()
