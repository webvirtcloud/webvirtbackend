import logging
import requests
from base64 import b64encode
from django.conf import settings

from virtance.models import Virtance
from .models import Compute


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

    def _make_get_url(self, url, stream=False):
        response = requests.get(url, headers=self._headers(), stream=stream, verify=False)
        return response

    def _make_post(self, url, params):
        url = self._url() + url
        response = requests.post(url, headers=self._headers(), json=params, verify=False)
        return response

    def _make_form_post(self, url, files=None):
        url = self._url() + url
        response = requests.post(url, headers=self._headers(), files=files, verify=False)
        return response

    def _make_put(self, url, params):
        url = self._url() + url
        response = requests.put(url, headers=self._headers(), json=params, verify=False)
        return response

    def _process_get(self, response, json=True):
        if response.status_code == 200:
            if json is True:
                body = response.json()
                if body is not None:
                    if isinstance(body, bytes) and hasattr(body, "decode"):
                        body = body.decode("utf-8")
                    return body
            else:
                return response.raw
        if 400 <= response.status_code:
            logging.exception(response.text)
        return {}

    def _process_post(self, response):
        if response.status_code == 201:
            body = response.json()
            if body:
                if isinstance(body, bytes) and hasattr(body, "decode"):
                    body = body.decode("utf-8")
                return body
        if 400 <= response.status_code:
            logging.exception(response.text)
        return {}

    def _process_put(self, response):
        if response.status_code == 204:
            body = response
            if body:
                if isinstance(body, bytes) and hasattr(body, "decode"):
                    body = body.decode("utf-8")
                return body
        if 400 <= response.status_code:
            logging.exception(response.text)
        return {}

    def create_virtance(self, id, uuid, vcpu, memory, images, network, keypairs, password):
        url = "virtances/"
        data = {
            "name": settings.VM_NAME_PREFIX + str(id),
            "uuid": uuid,
            "vcpu": vcpu,
            "memory": memory,
            "images": images,
            "network": network,
            "keypairs": keypairs,
            "root_password": password,
        }
        response = self._make_post(url, data)
        body = self._process_post(response)
        return body.get("virtance")
