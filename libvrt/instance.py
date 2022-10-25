import time
import libvirt
import os.path
from datetime import datetime
from xml.etree import ElementTree as ET

from .create import DISPLAY
from .connection import wvmConnect
from .util import get_xml_data, get_xml_findall


class wvmInstances(wvmConnect):
    def get_instance_status(self, name):
        inst = self.get_instance(name)
        return inst.info()[0]

    def get_instance_memory(self, name):
        inst = self.get_instance(name)
        mem = get_xml_data(inst.XMLDesc(), 'currentMemory')
        return int(mem) / 1024

    def get_instance_vcpu(self, name):
        inst = self.get_instance(name)
        cur_vcpu = get_xml_data(inst.XMLDesc(), 'vcpu', 'current')
        if cur_vcpu:
            vcpu = cur_vcpu
        else:
            vcpu = get_xml_data(inst.XMLDesc(), 'vcpu')
        return vcpu

    def get_instance_managed_save_image(self, name):
        inst = self.get_instance(name)
        return inst.hasManagedSaveImage()

    def get_uuid(self, name):
        inst = self.get_instance(name)
        return inst.UUIDString()

    def start(self, name):
        dom = self.get_instance(name)
        dom.create()

    def shutdown(self, name):
        dom = self.get_instance(name)
        dom.shutdown()

    def force_shutdown(self, name):
        dom = self.get_instance(name)
        dom.destroy()

    def managed_save(self, name):
        dom = self.get_instance(name)
        dom.managedSave(0)

    def managed_save_remove(self, name):
        dom = self.get_instance(name)
        dom.managedSaveRemove()

    def suspend(self, name):
        dom = self.get_instance(name)
        dom.suspend()

    def resume(self, name):
        dom = self.get_instance(name)
        dom.resume()

    def migrate(self, dconn, name, persist=False, undefine=False, disk=False):
        flags = 0
        dom = self.get_instance(name)
        if dom.get_status() == libvirt.VIR_DOMAIN_RUNNING:
            flags += libvirt.VIR_MIGRATE_LIVE
            flags += libvirt.VIR_MIGRATE_COMPRESSED
        if persist:
            flags += libvirt.VIR_MIGRATE_PERSIST_DEST
        if undefine:
            flags += libvirt.VIR_MIGRATE_UNDEFINE_SOURCE
        if disk:
            flags += libvirt.VIR_MIGRATE_NON_SHARED_DISK
        dom_migrated = dom.migrate(dconn, flags)
        dom_migrated.setAutostart(1)


class wvmInstance(wvmConnect):
    def __init__(self, host, login, passwd, conn, vname, keepalive=True):
        wvmConnect.__init__(self, host, login, passwd, conn, keepalive)
        self.instance = self.get_instance(vname)

    def get_status(self):
        return self.instance.info()[0]

    def start(self):
        self.instance.create()

    def shutdown(self):
        self.instance.shutdown()

    def force_shutdown(self):
        self.instance.destroy()

    def reboot(self):
        self.instance.destroy()
        self.instance.create()

    def managed_save(self):
        self.instance.managedSave()

    def managed_save_remove(self):
        self.instance.managedSaveRemove()

    def check_managed_save_image(self):
        return self.instance.hasManagedSaveImage()

    def suspend(self):
        self.instance.suspend()

    def resume(self):
        self.instance.resume()

    def delete(self):
        self.instance.undefineFlags(libvirt.VIR_DOMAIN_UNDEFINE_SNAPSHOTS_METADATA)

    def XMLDesc(self, flag=0):
        return self.instance.XMLDesc(flag)

    def defineXML(self, xml):
        return self.wvm.defineXML(xml)

    def attachDevice(self, xml, live=False):
        if self.get_status() == libvirt.VIR_DOMAIN_RUNNING:
            if live is True:
                self.instance.attachDeviceFlags(xml, libvirt.VIR_DOMAIN_AFFECT_LIVE)
            else:
                self.instance.attachDeviceFlags(xml, libvirt.VIR_DOMAIN_AFFECT_CURRENT)
            self.instance.attachDeviceFlags(xml, libvirt.VIR_DOMAIN_AFFECT_CONFIG)
        else:
            self.instance.attachDeviceFlags(xml, libvirt.VIR_DOMAIN_AFFECT_CONFIG)

    def updateDevice(self, xml, live=False):
        if self.get_status() == libvirt.VIR_DOMAIN_RUNNING:
            if live is True:
                self.instance.updateDeviceFlags(xml, libvirt.VIR_DOMAIN_AFFECT_LIVE)
            else:
                self.instance.updateDeviceFlags(xml, libvirt.VIR_DOMAIN_AFFECT_CURRENT)
            self.instance.updateDeviceFlags(xml, libvirt.VIR_DOMAIN_AFFECT_CONFIG)
        else:
            self.instance.updateDeviceFlags(xml, libvirt.VIR_DOMAIN_AFFECT_CONFIG)

    def detachDevice(self, xml, live=False):
        if self.get_status() == libvirt.VIR_DOMAIN_RUNNING:
            if live is True:
                self.instance.detachDeviceFlags(xml, libvirt.VIR_DOMAIN_AFFECT_LIVE)
            else:
                self.instance.detachDeviceFlags(xml, libvirt.VIR_DOMAIN_AFFECT_CURRENT)
            self.instance.detachDeviceFlags(xml, libvirt.VIR_DOMAIN_AFFECT_CONFIG)
        else:
            self.instance.detachDeviceFlags(xml, libvirt.VIR_DOMAIN_AFFECT_CONFIG)

    def get_power_state(self):
        if self.get_status() == libvirt.VIR_DOMAIN_RUNNING:
            return 'active'
        if self.get_status() == libvirt.VIR_DOMAIN_PAUSED:
            return 'suspend'
        if self.get_status() == libvirt.VIR_DOMAIN_SHUTOFF:
            return 'inactive'

    def get_autostart(self):
        return self.instance.autostart()

    def set_autostart(self, flag):
        return self.instance.setAutostart(flag)

    def get_uuid(self):
        return self.instance.UUIDString()

    def get_vcpu(self):
        vcpu = get_xml_data(self.XMLDesc(), 'vcpu')
        return int(vcpu)

    def get_cur_vcpu(self):
        cur_vcpu = get_xml_data(self.XMLDesc(), 'vcpu', 'current')
        if cur_vcpu:
            return int(cur_vcpu)

    def get_memory(self):
        mem = get_xml_data(self.XMLDesc(), 'memory')
        return int(mem) / 1024

    def get_cur_memory(self):
        mem = get_xml_data(self.XMLDesc(), 'currentMemory')
        return int(mem) / 1024

    def get_description(self):
        return get_xml_data(self.XMLDesc(), 'description')

    def get_max_memory(self):
        return self.wvm.getInfo()[1] * 1048576

    def get_max_cpus(self):
        """Get number of physical CPUs."""
        hostinfo = self.wvm.getInfo()
        pcpus = hostinfo[4] * hostinfo[5] * hostinfo[6] * hostinfo[7]
        range_pcpus = range(1, int(pcpus + 1))
        return range_pcpus

    def get_net_device(self):
        result = []

        def get_mac_ipaddr(xml, mac_host):
            tree = ET.fromstring(xml)
            for net in tree.findall('ip/dhcp/host'):
                if net.get('mac') == mac_host:
                    return net.get('ip')
            return None

        tree = ET.fromstring(self.XMLDesc())
        for interface in tree.findall('devices/interface'):
            ip_addr = None
            pool_name = None
            guest_mac = None
            guest_nic = None

            for dev in interface:
                if dev.tag == 'mac':
                    guest_mac = dev.get('address')
                if dev.tag == 'source':
                    pool_name = dev.get('network')
                    guest_nic = dev.get('network') or dev.get('bridge') or dev.get('dev')

            if pool_name:
                pool = self.get_network(pool_name)
                ip_addr = get_mac_ipaddr(pool.XMLDesc(), guest_mac)

            result.append({'ip': ip_addr, 'mac': guest_mac, 'nic': guest_nic, 'pool': pool_name})

        return result

    def get_disk_device(self):
        result = []
        tree = ET.fromstring(self.XMLDesc())
        for disks in tree.findall('devices/disk'):
            disk_img = None
            disk_dev = None
            disk_format = None

            if disks.get('device') == 'disk':
                for dev in disks:
                    if dev.tag == 'driver':
                        disk_format = dev.get('type')
                    if dev.tag == 'source':
                        disk_img = dev.get('file') or dev.get('dev') or dev.get('name') or dev.get('volume')
                    if dev.tag == 'target':
                        disk_dev = dev.get('dev')

                vol = self.get_volume_by_path(disk_img)
                stg = vol.storagePoolLookupByVolume()

                result.append({
                    'dev': disk_dev,
                    'image': vol.name(),
                    'storage': stg.name(),
                    'path': disk_img,
                    'format': disk_format,
                    'size': vol.info()[1],
                })

        return result

    def get_media_device(self):
        result = []
        tree = ET.fromstring(self.XMLDesc())
        for media in tree.findall('devices/disk'):
            vol_name = None
            stg_name = None
            disk_img = None
            disk_dev = None

            if media.get('device') == 'cdrom':
                for dev in media:
                    if dev.tag == 'target':
                        disk_dev = dev.get('dev')
                    if dev.tag == 'source':
                        disk_img = dev.get('file')

                if disk_dev and disk_img:
                    vol = self.get_volume_by_path(disk_img)
                    vol_name = vol.name()
                    stg = vol.storagePoolLookupByVolume()
                    stg_name = stg.name()

                result.append({
                    'dev': disk_dev,
                    'image': vol_name,
                    'storage': stg_name,
                    'path': disk_img,
                })

        return result

    def mount_iso(self, dev, image):
        vol_path = ''
        disk = """
            <disk type='file' device='cdrom'>
                <driver name='qemu'/>
                <target dev='hda' bus='ide'/>
                <readonly/>
                <serial>0</serial>
            </disk>
         """

        for storage in self.get_storages():
            stg = self.get_storage(storage)
            if stg.info()[0] != 0:
                for img in stg.listVolumes():
                    if image == img:
                        vol = stg.storageVolLookupByName(image)
                        vol_path = vol.path()
                        break

        tree = ET.fromstring(self.XMLDesc(libvirt.VIR_DOMAIN_XML_SECURE))
        for disk in tree.findall('devices/disk'):
            if disk.get('device') == 'cdrom':
                disk_target = disk.find('target')
                if disk_target.get('dev') == dev:
                    disk_source = disk.find('source')
                    if disk_source is None:
                        disk.append(ET.Element('source', file=vol_path))
                    else:
                        if disk_source.get('index'):
                            disk_source.set('file', vol_path)
                        else:
                            disk.append(ET.Element('source', file=vol_path))
                        break

        xmldev = ET.tostring(disk).decode()
        if self.get_status() == libvirt.VIR_DOMAIN_RUNNING:
            self.updateDevice(xmldev, live=True)
            xmldom = self.XMLDesc(libvirt.VIR_DOMAIN_XML_SECURE)

        if self.get_status() == libvirt.VIR_DOMAIN_SHUTOFF:
            self.updateDevice(xmldev, live=False)
            xmldom = ET.tostring(tree).decode()

        self.defineXML(xmldom)

    def umount_iso(self, dev, image_path):
        disk = """
            <disk type='file' device='cdrom'>
                <driver name='qemu' type='raw'/>
                <target dev='hda' bus='ide'/>
                <readonly/>
                <serial>0</serial>
              </disk>
        """

        tree = ET.fromstring(self.XMLDesc(libvirt.VIR_DOMAIN_XML_SECURE))
        for disk in tree.findall('devices/disk'):
            if disk.get('device') == 'cdrom':
                disk_target = disk.find('target')
                if disk_target.get('dev') == dev:
                    disk_source = disk.find('source')
                    if disk_source.get('file') == image_path:
                        disk.remove(disk_source)
                        if disk.find('backingStore'):
                            disk.remove(disk.find('backingStore'))
                        break

        xmldev = ET.tostring(disk).decode()
        if self.get_status() == libvirt.VIR_DOMAIN_RUNNING:
            self.updateDevice(xmldev, live=True)
            xmldom = self.XMLDesc(libvirt.VIR_DOMAIN_XML_SECURE)

        if self.get_status() == libvirt.VIR_DOMAIN_SHUTOFF:
            self.updateDevice(xmldev, live=False)
            xmldom = ET.tostring(tree).decode()

        self.defineXML(xmldom)

    def cpu_usage(self):
        usage = {'user': 0, 'total': 0, 'system': 0}
        if self.get_status() == libvirt.VIR_DOMAIN_RUNNING:
            nbcore = self.instance.info()[3]
            stats = self.instance.getCPUStats(True)
            user_ago = stats[0]['user_time']
            total_ago = stats[0]['cpu_time']
            system_ago = stats[0]['system_time']

            time.sleep(1)
            stats = self.instance.getCPUStats(True)
            user_now = stats[0]['user_time']
            total_now = stats[0]['cpu_time']
            system_now = stats[0]['system_time']

            diff_user = user_now - user_ago
            diff_total = total_now - total_ago
            diff_system = system_now - system_ago

            usage['user'] = 100 * diff_user / (nbcore * (10 ** 9))
            usage['total'] = 100 * diff_total / (nbcore * (10 ** 9))
            usage['system'] = 100 * diff_system / (nbcore * (10 ** 9))

            if usage['user'] > 100:
                usage['user'] = 100
            if usage['total'] > 100:
                usage['total'] = 100
            if usage['system'] > 100:
                usage['system'] = 100
        return usage

    def disk_usage(self):
        usage = []
        devices = []
        rd_diff_usage = 0
        wr_diff_usage = 0
        tree = ET.fromstring(self.XMLDesc())
        for disk in tree.findall('devices/disk'):
            if disk.get('device') == 'disk':
                dev_file = None
                dev_bus = None
                network_disk = True
                for elm in disk:
                    if elm.tag == 'source':
                        if elm.get('protocol'):
                            dev_file = elm.get('protocol')
                            network_disk = True
                        if elm.get('file'):
                            dev_file = elm.get('file')
                        if elm.get('dev'):
                            dev_file = elm.get('dev')
                    if elm.tag == 'target':
                        dev_bus = elm.get('dev')
                if (dev_file and dev_bus) is not None:
                    if network_disk:
                        dev_file = dev_bus
                    devices.append([dev_file, dev_bus])
        for dev in devices:
            if self.get_status() == libvirt.VIR_DOMAIN_RUNNING:
                rd_use_ago = self.instance.blockStats(dev[0])[1]
                wr_use_ago = self.instance.blockStats(dev[0])[3]

                time.sleep(1)
                rd_use_now = self.instance.blockStats(dev[0])[1]
                wr_use_now = self.instance.blockStats(dev[0])[3]

                rd_diff_usage = rd_use_now - rd_use_ago
                wr_diff_usage = wr_use_now - wr_use_ago
            usage.append({'dev': dev[1], 'rd': rd_diff_usage, 'wr': wr_diff_usage})
        return usage

    def net_usage(self):
        usage = []
        devices = []
        if self.get_status() == libvirt.VIR_DOMAIN_RUNNING:
            targets = get_xml_findall(self.XMLDesc(), 'devices/interface/target')
            for target in targets:
                devices.append(target.get("dev"))
            for i, dev in enumerate(devices):
                rx_use_ago = self.instance.interfaceStats(dev)[0]
                tx_use_ago = self.instance.interfaceStats(dev)[4]

                time.sleep(1)
                rx_use_now = self.instance.interfaceStats(dev)[0]
                tx_use_now = self.instance.interfaceStats(dev)[4]

                rx_diff_usage = (rx_use_now - rx_use_ago) * 8
                tx_diff_usage = (tx_use_now - tx_use_ago) * 8
                usage.append({'dev': i, 'rx': rx_diff_usage, 'tx': tx_diff_usage})
        else:
            for i, dev in enumerate(self.get_net_device()):
                usage.append({'dev': i, 'rx': 0, 'tx': 0})
        return usage

    def get_telnet_port(self):
        telnet_port = None
        service_port = None
        consoles = get_xml_findall(self.XMLDesc(), 'devices/console')
        for console in consoles:
            if console.get('type') == 'tcp':
                for elm in console:
                    if elm.tag == 'source':
                        if elm.get('service'):
                            service_port = elm.get('service')
                    if elm.tag == 'protocol':
                        if elm.get('type') == 'telnet':
                            if service_port is not None:
                                telnet_port = service_port
        return telnet_port

    def get_console_listen_addr(self):
        listen_addr = get_xml_data(self.XMLDesc(), 'devices/graphics', 'listen')
        if listen_addr is None:
            listen_addr = get_xml_data(self.XMLDesc(), 'devices/graphics/listen', 'address')
            if listen_addr is None:
                return "127.0.0.1"
        return listen_addr

    def get_console_socket(self):
        return get_xml_data(self.XMLDesc(), 'devices/graphics', 'socket')

    def get_console_type(self):
        return get_xml_data(self.XMLDesc(), 'devices/graphics', 'type')

    def set_console_type(self, console_type):
        current_type = self.get_console_type()
        if current_type == console_type:
            return True
        if console_type == '' or console_type not in DISPLAY:
            return False
        xml = self.XMLDesc(libvirt.VIR_DOMAIN_XML_SECURE)
        root = ET.fromstring(xml)
        try:
            graphic = root.find(f"devices/graphics[@type='{current_type}']")
        except SyntaxError:
            # Little fix for old version ET
            graphic = root.find("devices/graphics")
        graphic.set('type', console_type)
        newxml = ET.tostring(root)
        self.defineXML(newxml)

    def get_console_port(self, console_type=None):
        if console_type is None:
            console_type = self.get_console_type()
        return get_xml_data(self.XMLDesc(), f"devices/graphics[@type='{console_type}']", 'port')

    def get_console_websocket_port(self):
        console_type = self.get_console_type()
        return get_xml_data(self.XMLDesc(), f"devices/graphics[@type='{console_type}']", 'websocket')

    def get_console_passwd(self):
        return get_xml_data(self.XMLDesc(libvirt.VIR_DOMAIN_XML_SECURE), 'devices/graphics', 'passwd')

    def set_console_passwd(self, passwd):
        xml = self.XMLDesc(libvirt.VIR_DOMAIN_XML_SECURE)
        root = ET.fromstring(xml)
        console_type = self.get_console_type()
        try:
            graphic = root.find(f"devices/graphics[@type='{console_type}']")
        except SyntaxError:
            # Little fix for old version ET
            graphic = root.find("devices/graphics")
        if graphic is None:
            return False
        if passwd:
            graphic.set('passwd', passwd)
        else:
            try:
                graphic.attrib.pop('passwd')
            except ET:
                pass
        newxml = ET.tostring(root)
        return self.defineXML(newxml)

    def set_console_keymap(self, keymap):
        xml = self.XMLDesc(libvirt.VIR_DOMAIN_XML_SECURE)
        root = ET.fromstring(xml)
        console_type = self.get_console_type()
        try:
            graphic = root.find(f"devices/graphics[@type='{console_type}']")
        except SyntaxError:
            # Little fix for old version ET
            graphic = root.find("devices/graphics")
        if keymap:
            graphic.set('keymap', keymap)
        else:
            try:
                graphic.attrib.pop('keymap')
            except ET:
                pass
        newxml = ET.tostring(root)
        self.defineXML(newxml)

    def get_console_keymap(self):
        return (
            get_xml_data(self.XMLDesc(libvirt.VIR_DOMAIN_XML_SECURE), 'devices/graphics', 'keymap',) or ''
        )

    def resize_resources(self, vcpu, memory, current_vcpu=None, current_memory=None):
        """
        Function change ram and cpu on vds.
        """
        memory = round(memory / 1024)
        if current_memory is None:
            current_memory = memory
        else:
            current_memory = round(current_memory / 1024)
        self.instance.setMaxMemory(memory)
        self.instance.setMemoryFlags(current_memory, libvirt.VIR_DOMAIN_AFFECT_CONFIG)

        if current_vcpu is None:
            current_vcpu = vcpu
        vcpu_flags = libvirt.VIR_DOMAIN_VCPU_MAXIMUM + libvirt.VIR_DOMAIN_AFFECT_CONFIG
        self.instance.setVcpusFlags(vcpu, vcpu_flags)
        self.instance.setVcpusFlags(current_vcpu, libvirt.VIR_DOMAIN_VCPU_CURRENT)

    def add_private_iface(self, ipaddr, net_pool, mac=None):
        xml = """<interface type='network'>"""
        if mac:
            xml += f"""<mac address='{mac}'/>"""
        xml += f"""<source network='{net_pool}'/>
                  <model type='virtio'/>
                  <filterref filter='clean-traffic'>
                     <parameter name='IP' value='{ipaddr}'/>
                  </filterref>
                  </interface>"""
        self.attachDevice(xml)

    def add_rbd_disk(self, path, hosts, username, uuid, dev='vdb', serial=0):
        xml = f"""<disk type='network' path='disk'>
                    <driver name='qemu' type='raw' cache='writeback'/>
                    <source protocol='rbd' name='{path}'>"""
        for host in hosts:
            xml += f"""<host name='{host}' port='6789'/>"""
        xml += f"""</source>
                     <auth username='{username}'>
                        <secret type='ceph' uuid='{uuid}'/>
                    </auth>
                    <target dev='{dev}' bus='virtio'/>
                    <serial>QEMU_VOLUME_{serial}</serial>
                  </disk>"""
        self.attachDevice(xml)

    def del_rbd_disk(self):
        xml = self.XMLDesc(libvirt.VIR_DOMAIN_XML_SECURE)
        tree = ET.fromstring(xml)
        for disk in tree.findall('devices/disk'):
            if disk.get('type') == 'network':
                xml_disk = ET.tostring(disk)
                self.detachDevice(xml_disk.decode())

    def get_iso_media(self):
        iso = []
        storages = self.get_storages()
        for storage in storages:
            stg = self.get_storage(storage)
            if stg.info()[0] != 0:
                try:
                    stg.refresh(0)
                except libvirt.libvirtError:
                    pass
                for img in stg.listVolumes():
                    if img.endswith('.iso'):
                        iso.append(img)
        return iso

    def delete_disk(self, dev=None):
        disks = self.get_disk_device()
        if dev:
            for disk in disks:
                if disk['dev'] == dev:
                    vol = self.get_volume_by_path(disk.get('path'))
                    vol.delete(0)
        else:
            for disk in disks:
                vol = self.get_volume_by_path(disk.get('path'))
                vol.delete(0)

    def _snapshotCreateXML(self, xml, flag):
        self.instance.snapshotCreateXML(xml, flag)

    def create_snapshot(self, name):
        xml_dom = self.XMLDesc()
        rbd_disk = False
        tree = ET.fromstring(xml_dom)
        for disk in tree.findall('devices/disk'):
            if disk.get('type') == 'network':
                xml_disk = ET.tostring(disk)
                rbd_disk = True
        if rbd_disk:
            self.detachDevice(xml_disk)
        xml = f"""<domainsnapshot>
                     <name>{name}</name>
                     <state>shutoff</state>
                     <creationTime>{time.time():d}</creationTime>
                     <memory snapshot='no'/>"""
        xml += self.XMLDesc(libvirt.VIR_DOMAIN_XML_SECURE)
        xml += """</domainsnapshot>"""
        self._snapshotCreateXML(xml, 0)
        if rbd_disk:
            self.attachDevice(xml_disk)

    def get_snapshot(self):
        snapshots = []
        snapshot_list = self.instance.snapshotListNames(0)
        for snapshot in snapshot_list:
            snap = self.instance.snapshotLookupByName(snapshot, 0)
            snap_time_create = get_xml_data(snap.getXMLDesc(), 'creationTime')
            snapshots.append(
                {
                    'date': datetime.fromtimestamp(int(snap_time_create)),
                    'name': snapshot,
                }
            )
        return snapshots

    def snapshot_delete(self, snapshot):
        snap = self.instance.snapshotLookupByName(snapshot, 0)
        snap.delete(0)

    def snapshot_revert(self, snapshot):
        xml_dom = self.XMLDesc()
        rbd_disk = False
        tree = ET.fromstring(xml_dom)
        for disk in tree.findall('devices/disk'):
            if disk.get('type') == 'network':
                xml_disk = ET.tostring(disk)
                rbd_disk = True
        if rbd_disk:
            self.detachDevice(xml_disk)
        snap = self.instance.snapshotLookupByName(snapshot, 0)
        self.instance.revertToSnapshot(snap, 0)
        if rbd_disk:
            self.attachDevice(xml_disk)

    def get_managed_save_image(self):
        return self.instance.hasManagedSaveImage(0)

    def clone_instance(self, clone_data):
        clone_dev_path = []
        xml = self.XMLDesc(libvirt.VIR_DOMAIN_XML_SECURE)
        tree = ET.fromstring(xml)
        name = tree.find('name')
        name.text = clone_data['name']
        uuid = tree.find('uuid')
        tree.remove(uuid)

        for num, net in enumerate(tree.findall('devices/interface')):
            elm = net.find('mac')
            elm.set('address', clone_data['net-' + str(num)])

        for disk in tree.findall('devices/disk'):
            if disk.get('device') == 'disk':
                elm = disk.find('target')
                device_name = elm.get('dev')
                if device_name:
                    target_file = clone_data['disk-' + device_name]
                    try:
                        meta_prealloc = clone_data['meta-' + device_name]
                    except Exception:
                        meta_prealloc = False
                    elm.set('dev', device_name)

                elm = disk.find('source')
                source_file = elm.get('file')
                if source_file:
                    clone_dev_path.append(source_file)
                    clone_path = os.path.join(os.path.dirname(source_file), target_file)
                    elm.set('file', clone_path)

                    vol = self.get_volume_by_path(source_file)
                    vol_format = get_xml_data(vol.XMLDesc(), 'target/format', 'type')

                    if vol_format == 'qcow2' and meta_prealloc:
                        meta_prealloc = True
                    vol_clone_xml = f"""
                                    <volume>
                                        <name>{target_file}</name>
                                        <capacity>0</capacity>
                                        <allocation>0</allocation>
                                        <target>
                                            <format type='{vol_format}'/>
                                        </target>
                                    </volume>"""
                    stg = vol.storagePoolLookupByVolume()
                    stg.createXMLFrom(vol_clone_xml, vol, meta_prealloc)

        self.defineXML(ET.tostring(tree))

    def migrate(self, dconn, persist=False, undefine=False, disk=False):
        flags = 0
        if self.get_status() == libvirt.VIR_DOMAIN_RUNNING:
            flags += libvirt.VIR_MIGRATE_LIVE
        if persist:
            flags += libvirt.VIR_MIGRATE_PERSIST_DEST
        if undefine:
            flags += libvirt.VIR_MIGRATE_UNDEFINE_SOURCE
        if disk:
            flags += libvirt.VIR_MIGRATE_NON_SHARED_DISK
        dom = self.instance.migrate(dconn, flags)
        dom.setAutostart(1)
