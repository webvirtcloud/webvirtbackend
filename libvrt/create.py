import string
from IPy import IP
from libvirt import libvirtError

from .connection import wvmConnect
from .storage import get_rbd_storage_data
from .util import get_xml_data, gen_password


# Default settings
DISPLAY = "vnc"
VENDOR = "WebVirtCloud"
PRODUCT = "WebVirtCloud"
MANUFACTURER = "WebVirtCloud"


class wvmCreate(wvmConnect):
    def get_storages_images(self):
        """
        Function return all images on all storages
        """
        images = []
        storages = self.get_storages()
        for storage in storages:
            stg = self.get_storage(storage)
            try:
                stg.refresh(0)
            except libvirtError:
                pass
            for img in stg.listVolumes():
                if img.endswith(".iso"):
                    pass
                else:
                    images.append(img)
        return images

    def get_os_type(self):
        """Get guest capabilities"""
        return get_xml_data(self.get_cap_xml(), "guest/os_type")

    def get_host_arch(self):
        """Get guest capabilities"""
        return get_xml_data(self.get_cap_xml(), "host/cpu/arch")

    def create_volume(self, storage, name, size, volume_format="qcow2", metadata=False):
        stg = self.get_storage(storage)
        storage_type = get_xml_data(stg.XMLDesc(0), element="type")
        if storage_type == "dir":
            name = f"{name}.img"
            alloc = 0
        else:
            alloc = size
            metadata = False
        xml = f"""
                <volume>
                    <name>{name}</name>
                    <capacity>{size}</capacity>
                    <allocation>{alloc}</allocation>
                    <target>
                        <format type='{volume_format}'/>
                    </target>
                </volume>"""
        stg.createXML(xml, metadata)
        try:
            stg.refresh(0)
        finally:
            vol = stg.storageVolLookupByName(name)
            return vol.path()

    def get_volume_type(self, path):
        vol = self.get_volume_by_path(path)
        vol_type = get_xml_data(vol.XMLDesc(0), "target/format", "type")
        if vol_type == "unknown":
            return "raw"
        if vol_type:
            return vol_type
        else:
            return "raw"

    def get_volume_path(self, volume):
        storages = self.get_storages()
        for storage in storages:
            stg = self.get_storage(storage)
            if stg.info()[0] != 0:
                stg.refresh(0)
                for img in stg.listVolumes():
                    if img == volume:
                        vol = stg.storageVolLookupByName(img)
                        return vol.path()

    def get_storage_by_vol_path(self, vol_path):
        vol = self.get_volume_by_path(vol_path)
        return vol.storagePoolLookupByVolume()

    def clone_from_template(self, clone, template, metadata=False):
        vol = self.get_volume_by_path(template)
        stg = vol.storagePoolLookupByVolume()
        storage_type = get_xml_data(stg.XMLDesc(0), element="type")
        vol_type = get_xml_data(vol.XMLDesc(0), "target/format", "type")
        if storage_type == "dir":
            clone += ".img"
        else:
            metadata = False
        xml = f"""
                <volume>
                    <name>{clone}</name>
                    <capacity>0</capacity>
                    <allocation>0</allocation>
                    <target>
                        <format type='{vol_type}'/>
                    </target>
                </volume>"""
        stg.createXMLFrom(xml, vol, metadata)
        clone_vol = stg.storageVolLookupByName(clone)
        return clone_vol.path()

    def defineXML(self, xml):
        self.wvm.defineXML(xml)

    def delete_volume(self, path):
        vol = self.get_volume_by_path(path)
        vol.delete()

    def create_instance(
        self,
        name,
        vcpu,
        memory,
        images,
        network,
        autostart=False,
        nwfilter=True,
        display=DISPLAY,
    ):
        """
        Create VM function
        """
        xml = f"""
                <domain type='{'kvm' if self.is_kvm_supported() else 'qemu'}'>
                  <name>{name}</name>
                  <description>None</description>
                  <memory unit='KiB'>{int(memory / 1024)}</memory>
                  <vcpu>{vcpu}</vcpu>"""

        if self.is_kvm_supported():
            xml += """<cpu mode='host-passthrough'/>"""

        xml += f"""<sysinfo type='smbios'>
                    <bios>
                      <entry name='vendor'>SimplyStack Cloud</entry>
                      <entry name='version'>20171909</entry>
                      <entry name='date'>11/03/2017</entry>
                    </bios>
                    <system>
                     <entry name='manufacturer'>SimplyStack</entry>
                      <entry name='product'>Stacklet</entry>
                      <entry name='version'>20171909</entry>
                      <entry name='serial'>{name.split('-')[1]}</entry>
                      <entry name='family'>SimplyStack_Stacklet</entry>
                    </system>
                   </sysinfo>"""

        xml += f"""<os>
                    <type arch='{self.get_host_arch()}'>{self.get_os_type()}</type>
                    <boot dev='cdrom'/>
                    <boot dev='hd'/>
                    <smbios mode='sysinfo'/>
                   </os>"""

        xml += """<features>
                   <acpi/><apic/><pae/>
                  </features>

                  <clock offset="utc"/>
                  <on_poweroff>destroy</on_poweroff>
                  <on_reboot>restart</on_reboot>
                  <on_crash>restart</on_crash>
                  <devices>"""

        disk_letters = list(string.ascii_lowercase)
        for image, img_type in images.items():
            disk_letter = disk_letters.pop(0)
            stg = self.get_storage_by_vol_path(image)
            stg_type = get_xml_data(stg.XMLDesc(0), element="type")

            if stg_type == "rbd":
                ceph_user, secret_uuid, ceph_host = get_rbd_storage_data(stg)

                xml += f"""<disk type='network' device='disk'>
                            <driver name='qemu' type='{img_type}' cache='writeback'/>
                            <auth username='{ceph_user}'>
                             <secret type='ceph' uuid='{secret_uuid}'/>
                            </auth>
                            <source protocol='rbd' name='{image}'>
                             <host name='{ceph_host}' port='6789'/>
                            </source>
                            <serial>QEMU_VOLUME_0</serial>
                           </disk>"""
            else:
                xml += f"""<disk type='file' device='disk'>
                            <driver name='qemu' type='{img_type}'/>
                            <source file='{image}'/>
                            <target dev='vd{disk_letter}' bus='virtio'/>
                            <serial>QEMU_DISK_0</serial>
                           </disk>"""

        xml += """<disk type='file' device='cdrom'>
                   <driver name='qemu' type='raw'/>
                   <source file=''/>
                   <target dev='hda' bus='ide'/>
                   <readonly/>
                   <serial>0</serial>
                  </disk>"""

        # Create public pool device with IP and IPv6 and Anchor
        if network.get("public_ipv4_address"):
            xml += f"""<interface type='network'>
                        <mac address='{network.get('public_device_mac')}'/>
                        <source network='{network.get('public_pool')}'/>"""
            if nwfilter:
                xml += """<filterref filter='clean-traffic-ipv6'>"""

                if network.get("public_ipv4_anchor"):
                    xml += f"""<parameter name='IP' value='{network.get('public_ipv4_address')}'/>"""

                if network.get("public_ipv4_anchor"):
                    xml += f"""<parameter name='IP' value='{network.get('public_ipv4_anchor')}'/>"""

                if network.get("public_ipv6_range"):
                    for ipv6 in IP(network["public_ipv6_range"]):
                        xml += f"""<parameter name='IPV6' value='{ipv6.strNormal()}'/>"""

                xml += """</filterref>"""

            xml += """<model type='virtio'/>
                      </interface>"""

        # Create private pool device with IP
        if network.get("private_ipv4_address"):
            xml += f"""<interface type='network'>
                        <mac address='{network.get('private_device_mac')}'/>
                        <source network='{network.get('private_pool')}'/>"""
            if nwfilter:
                xml += f"""<filterref filter='clean-traffic'>
                            <parameter name='IP' value='{network.get('private_ipv4_address')}'/>
                           </filterref>"""

            xml += """<model type='virtio'/>
                      </interface>"""

        # Create vpc device for VPC
        if network.get("vpc_ipv4_address"):
            xml += f"""<interface type='bridge'>
                        <mac address='{network.get('vpc_device_mac')}'/>
                        <source bridge='{network.get('vpc_device')}'/>"""

            if nwfilter:
                xml += f"""<filterref filter='clean-traffic'>
                            <parameter name='IP' value='{network.get('vpc_ipv4_address')}'/>
                           </filterref>"""

            xml += """<model type='virtio'/>
                      </interface>"""

        # Create public pool device without public IP
        if network.get("public_ipv4_anchor") and not network.get("public_ipv4_address"):
            xml += f"""<interface type='network'>
                        <mac address='{network.get('public_mac')}'/>
                        <source network='{network.get('public_pool')}'/>"""
            if nwfilter:
                xml += f"""<filterref filter='clean-traffic'>
                            <parameter name='IP' value='{network.get('public_ipv4_anchor')}'/>
                           </filterref>"""

            xml += """<model type='virtio'/>
                      </interface>"""

        xml += f"""<input type='mouse' bus='ps2'/>
                   <input type='tablet' bus='usb'/>
                   <graphics type='{display}' port='-1' autoport='yes'
                    listen='0.0.0.0' passwd='{gen_password(length=8)}'>
                    <listen type='address' address='0.0.0.0'/>
                   </graphics>
                   <console type='pty'/>
                   <model type='cirrus' heads='1'>
                    <acceleration accel3d='yes' accel2d='yes'/>
                   </model>
                   <memballoon model='virtio'/>
                   </devices>
                   </domain>"""

        self.defineXML(xml)

        if autostart:
            dom = self.get_instance(name)
            dom.setAutostart(1)
