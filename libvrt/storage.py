from .connection import wvmConnect
from .util import get_xml_data, pretty_bytes


def get_rbd_storage_data(stg):
    hosts = []
    xml = stg.XMLDesc(0)
    host_count = xml.find("host")
    username = get_xml_data(xml, "source/auth", "username")
    uuid = get_xml_data(xml, "source/auth/secret", "uuid")
    for i in range(1, host_count + 1):
        host = get_xml_data(xml, f"source/host[{i}]", "name")
        if host:
            hosts.append(host)
    return username, uuid, hosts


class wvmStorages(wvmConnect):
    def get_storages_info(self):
        get_storages = self.get_storages()
        storages = []
        for pool in get_storages:
            stg = self.get_storage(pool)
            stg_status = stg.isActive()
            stg_type = get_xml_data(stg.XMLDesc(0), element="type")
            if stg_status:
                stg_vol = len(stg.listVolumes())
            else:
                stg_vol = None
            stg_size = stg.info()[1]
            storages.append(
                {
                    "name": pool,
                    "status": stg_status,
                    "type": stg_type,
                    "volumes": stg_vol,
                    "size": stg_size,
                }
            )
        return storages

    def define_storage(self, xml, flag):
        self.wvm.storagePoolDefineXML(xml, flag)

    def create_storage(self, stg_type, name, source, target):
        xml = f"""
                <pool type='{stg_type}'>
                <name>{name}</name>"""
        if stg_type == "logical":
            xml += f"""
                  <source>
                    <device path='{source}'/>
                    <name>{name}</name>
                    <format type='lvm2'/>
                  </source>"""
        if stg_type == "logical":
            target = "/dev/" + name
        xml += f"""
                  <target>
                       <path>{target}</path>
                  </target>
                </pool>"""
        self.define_storage(xml, 0)
        stg = self.get_storage(name)
        if stg_type == "logical":
            stg.build(0)
        stg.create(0)
        stg.setAutostart(1)

    def create_storage_ceph(self, stg_type, name, pool, host1, host2, host3, user, secret):
        xml = f"""
                <pool type='{stg_type}'>
                <name>{name}</name>
                <source>
                    <name>{pool}</name>
                    <host name='{host1}' port='6789'/>"""
        if host2:
            xml += f"""<host name='{host2}' port='6789'/>"""
        if host3:
            xml += f"""<host name='{host3}' port='6789'/>"""

        xml += """<auth username='%s' type='ceph'>
                        <secret uuid='%s'/>
                    </auth>
                </source>
                </pool>""" % (
            user,
            secret,
        )
        self.define_storage(xml, 0)
        stg = self.get_storage(name)
        stg.create(0)
        stg.setAutostart(1)

    def create_storage_netfs(self, stg_type, name, netfs_host, source, source_format, target):
        xml = f"""
                <pool type='{stg_type}'>
                <name>{name}</name>
                <source>
                    <host name='{netfs_host}'/>
                    <dir path='{source}'/>
                    <format type='{source_format}'/>
                </source>
                <target>
                    <path>{target}</path>
                </target>
                </pool>"""
        self.define_storage(xml, 0)
        stg = self.get_storage(name)
        stg.create(0)
        stg.setAutostart(1)


class wvmStorage(wvmConnect):
    def __init__(self, host, login, passwd, conn, pool, keepalive=True):
        wvmConnect.__init__(self, host, login, passwd, conn, keepalive)
        self.pool = self.get_storage(pool)

    def get_name(self):
        return self.pool.name()

    def get_status(self):
        status = [
            "Not running",
            "Initializing pool, not available",
            "Running normally",
            "Running degraded",
        ]
        try:
            return status[self.pool.info()[0]]
        except ValueError:
            return "Unknown"

    def get_size(self):
        return [self.pool.info()[1], self.pool.info()[3]]

    def XMLDesc(self, flags):
        return self.pool.XMLDesc(flags)

    def createXML(self, xml, flags):
        self.pool.createXML(xml, flags)

    def createXMLFrom(self, xml, vol, flags):
        self.pool.createXMLFrom(xml, vol, flags)

    def define(self, xml):
        return self.wvm.storagePoolDefineXML(xml, 0)

    def is_active(self):
        return self.pool.isActive()

    def get_uuid(self):
        return self.pool.UUIDString()

    def start(self):
        self.pool.create(0)

    def stop(self):
        self.pool.destroy()

    def delete(self):
        self.pool.undefine()

    def get_autostart(self):
        return self.pool.autostart()

    def set_autostart(self, value):
        self.pool.setAutostart(value)

    def get_type(self):
        return get_xml_data(self.XMLDesc(0), element="type")

    def get_target_path(self):
        return get_xml_data(self.XMLDesc(0), "target/path")

    def get_allocation(self):
        return int(get_xml_data(self.XMLDesc(0), "allocation"))

    def get_available(self):
        return int(get_xml_data(self.XMLDesc(0), "available"))

    def get_capacity(self):
        return int(get_xml_data(self.XMLDesc(0), "capacity"))

    def get_pretty_allocation(self):
        return pretty_bytes(self.get_allocation())

    def get_pretty_available(self):
        return pretty_bytes(self.get_available())

    def get_pretty_capacity(self):
        return pretty_bytes(self.get_capacity())

    def get_volumes(self):
        return self.pool.listVolumes()

    def get_volume(self, name):
        return self.pool.storageVolLookupByName(name)

    def get_volume_size(self, name):
        vol = self.get_volume(name)
        return vol.info()[1]

    def _vol_XMLDesc(self, name):
        vol = self.get_volume(name)
        return vol.XMLDesc(0)

    def del_volume(self, name):
        vol = self.pool.storageVolLookupByName(name)
        vol.delete(0)

    def get_volume_type(self, name):
        return get_xml_data(self._vol_XMLDesc(name), "target/format", "type")

    def refresh(self):
        self.pool.refresh(0)

    def update_volumes(self):
        try:
            self.refresh()
        except Exception:
            pass
        vols = self.get_volumes()
        vol_list = []

        for vol_name in vols:
            vol_list.append(
                {
                    "name": vol_name,
                    "size": self.get_volume_size(vol_name),
                    "type": self.get_volume_type(vol_name),
                }
            )
        return vol_list

    def create_volume(self, name, size, vol_fmt="qcow2", metadata=False):
        storage_type = self.get_type()
        alloc = size
        if vol_fmt == "unknown":
            vol_fmt = "raw"
        if storage_type == "dir":
            name += ".img"
            alloc = 0
        xml = f"""
            <volume>
                <name>{name}</name>
                <capacity>{size}</capacity>
                <allocation>{alloc}</allocation>
                <target>
                    <format type='{vol_fmt}'/>
                </target>
            </volume>"""
        self.createXML(xml, metadata)

    def clone_volume(self, name, clone, vol_fmt=None, metadata=False):
        storage_type = self.get_type()
        if storage_type == "dir":
            clone += ".img"
        vol = self.get_volume(name)
        if not vol_fmt:
            vol_fmt = self.get_volume_type(name)
        xml = f"""
            <volume>
                <name>{clone}</name>
                <capacity>0</capacity>
                <allocation>0</allocation>
                <target>
                    <format type='{vol_fmt}'/>
                </target>
            </volume>"""
        self.createXMLFrom(xml, vol, metadata)
