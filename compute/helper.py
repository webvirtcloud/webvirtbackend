import requests
from base64 import b64encode
from django.conf import settings
from urllib.parse import urlencode

from virtance.models import Virtance
from .models import Compute


def vm_name(virtance_id):
    return f"{settings.VM_NAME_PREFIX}{str(virtance_id)}"


def assign_free_compute(virtance_id):
    virtance = Virtance.objects.get(id=virtance_id)
    computes = Compute.objects.filter(
        region=virtance.region, is_active=True, is_deleted=False
    ).order_by("?")
    for compute in computes: # TODO: check if compute is available
        virtance.compute = compute
        virtance.save()
        return True
    return False


class WebVirtCompute(object):
    def __init__(self, token, host, secure=False):
        self.port = settings.COMPUTE_PORT
        self.host = host
        self.token = token
        self.secure = secure

    def _url(self):
        return f"http{'s' if self.secure else ''}://{self.host}:{self.port}/"

    def _headers(self):
        credentials = f"{self.token}:{self.token}"
        return {
            "Accept": "application/json, */*",
            "Content-Type": "application/json",
            "Authorization": f"Basic {b64encode(credentials.encode()).decode()}",
        }

    def _make_get(self, query, stream=False):
        url = self._url() + query
        response = requests.get(url, headers=self._headers(), stream=stream, verify=False)
        return response

    def _make_post(self, url, params):
        url = self._url() + url
        response = requests.post(url, headers=self._headers(), json=params, verify=False)
        return response

    def _make_put(self, url, params):
        url = self._url() + url
        response = requests.put(url, headers=self._headers(), json=params, verify=False)
        return response

    def _make_delete(self, url):
        url = self._url() + url
        response = requests.delete(url, headers=self._headers(), verify=False)
        return response

    def _process_response(self, response, json=True):
        if response.status_code == 204:
            return {}
        if json:
            body = response.json()
            if body:
                if isinstance(body, bytes) and hasattr(body, "decode"):
                    body = body.decode("utf-8")
                return body
        return response.raw

    def create_virtance(self, id, uuid, hostname, vcpu, memory, images, network, keypairs, password):
        url = "virtances/"
        data = {
            "name": vm_name(id),
            "uuid": uuid,
            "hostname": hostname,
            "vcpu": vcpu,
            "memory": memory,
            "images": images,
            "network": network,
            "keypairs": keypairs,
            "root_password": password,
        }
        response = self._make_post(url, data)
        body = self._process_response(response)
        return body.get("virtance")

    def status_virtance(self, id):
        url = f"virtances/{vm_name(id)}/status/"
        response = self._make_get(url)
        body = self._process_response(response)
        return body.get("status")

    def get_virtance_vnc(self, id):
        url = f"virtances/{vm_name(id)}/vnc/"
        response = self._make_get(url)
        body = self._process_response(response)
        return body

    def action_virtance(self, id, action):
        url = f"virtances/{vm_name(id)}/status/"
        response = self._make_post(url, {"action": action})
        body = self._process_response(response)
        return body.get("status")

    def delete_virtance(self, id):
        url = f"virtances/{vm_name(id)}/"
        response = self._make_response(url)
        body = self._process_response(response)
        return body.get("virtance")

    def get_host_overview(self):
        url = "host/"
        response = self._make_get(url)
        body = self._process_response(response)
        return body
    
    def create_storage_dir(self, name, target):
        url = f"storages/"
        payload = {"type": "dir", "name": name, "target": target}
        response = self._make_post(url, payload)
        body = self._process_response(response)
        return body

    def create_storage_rbd(self, name, pool, user, secret, host, host2=None, host3=None):
        url = f"storages/"
        payload = {
            "type": "rbd",
            "name": name, 
            "pool": pool, 
            "user": user,
            "host": host,
            "host2": host2,
            "host3": host3,
            "secret": secret
        }
        response = self._make_post(url, payload)
        body = self._process_response(response)
        return body

    def get_storages(self):
        url = "storages/"
        response = self._make_get(url)
        body = self._process_response(response)
        return body.get("storages")

    def get_storage(self, pool):
        url = f"storages/{pool}/"
        response = self._make_get(url)
        body = self._process_response(response)
        return body.get("storage")

    def delete_storage(self, pool):
        url = f"storages/{pool}/"
        response = self._make_delete(url)
        body = self._process_response(response)
        return body

    def set_storage_action(self, pool, action):
        url = f"storages/{pool}/"
        action = {"action": action}
        response = self._make_post(url, action)
        body = self._process_response(response)
        return body

    def create_storage_volume(self, pool, name, size, format="qcow2"):
        url = f"storages/{pool}/volumes/"
        payload = {"name": name, "size": size, "format": format}
        response = self._make_post(url, payload)
        body = self._process_response(response)
        return body

    def action_storage_volume(self, pool, name, action, data):
        url = f"storages/{pool}/volumes/{name}/"
        if action == "resize":
            var = "size"
        if action == "clone":
            var = "name"
        params = {"action": action, var: data}
        response = self._make_post(url, params)
        body = self._process_response(response)
        return body

    def delete_storage_volume(self, pool, name):
        url = f"storages/{pool}/volumes/{name}/"
        response = self._make_delete(url)
        body = self._process_response(response)
        return body

    def create_network(self, name, interface, openvswitch):
        url = "networks/"
        payload = {
            "name": name,
            "forward": "bridge",
            "gateway": None,
            "mask": None,
            "dhcp": None,
            "bridge": interface,
            "openvswitch": openvswitch
        }
        response = self._make_post(url, payload)
        body = self._process_response(response)
        return body

    def get_networks(self):
        url = "networks/"
        response = self._make_get(url)
        body = self._process_response(response)
        return body.get("networks")

    def get_network(self, net):
        url = f"networks/{net}/"
        response = self._make_get(url)
        body = self._process_response(response)
        return body.get("network")

    def delete_network(self, net):
        url = f"networks/{net}"
        response = self._make_delete(url)
        body = self._process_response(response)
        return body

    def set_network_action(self, pool, action):
        url = f"networks/{pool}/"
        action = {"action": action}
        response = self._make_post(url, action)
        body = self._process_response(response)
        return body

    def get_interfaces(self):
        url = "interfaces/"
        response = self._make_get(url)
        body = self._process_response(response)
        return body.get("interfaces")

    def get_secrets(self):
        url = "secrets/"
        response = self._make_get(url)
        body = self._process_response(response)
        return body.get("secrets")

    def create_secret(self, ephemeral, private, type, data):
        url = "secrets/"
        payload = {
            "ephemeral": ephemeral, 
            "private": private, 
            "type": type,
            "data": data
        }
        response = self._make_post(url, payload)
        body = self._process_response(response)
        return body

    def get_secret(self, uuid):
        url = f"secrets/{uuid}/"
        response = self._make_get(url)
        body = self._process_response(response)
        return body.get("secret")

    def update_secret_value(self, uuid, value):
        url = f"secrets/{uuid}"
        response = self._make_post(url, {"value": value})
        body = self._process_response(response)
        return body

    def delete_secret(self, uuid):
        url = f"secrets/{uuid}/"
        response = self._make_delete(url)
        body = self._process_response(response)
        return body

    def get_nwfilters(self):
        url = "nwfilters/"
        response = self._make_get(url)
        body = self._process_response(response)
        return body.get("nwfilters")

    def create_nwfilter(self, xml):
        url = "nwfilters/"
        response = self._make_post(url, {"xml": xml})
        body = self._process_response(response)
        return body

    def view_nwfilter(self, name):
        url = f"nwfilters/{name}/"
        response = self._make_get(url)
        body = self._process_response(response)
        return body.get("nwfilter")

    def delete_nwfilter(self, name):
        url = f"nwfilters/{name}/"
        response = self._make_delete(url)
        body = self._process_response(response)
        return body

    def get_metrics(self, query, start, end, step):
        url = f"metrics/"
        params = {"query": query, "start": start, "end": end, "step": step}
        response = self._make_get(f"{url}?{urlencode(params)}")
        body = self._process_response(response)
        return body
