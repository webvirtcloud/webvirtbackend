import time
from django.conf import settings
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response

from compute.helper import WebVirtCompute
from .utils import make_vnc_hash
from .models import Virtance
from .tasks import delete_virtance
from .serializers import VirtanceSerializer, CreateVirtanceSerializer, VirtanceActionSerializer


class VirtanceListAPI(APIView):
    class_serializer = VirtanceSerializer

    def get(self, request, *args, **kwargs):
        virtances = Virtance.objects.filter(user=request.user, is_deleted=False)
        serilizator = self.class_serializer(virtances, many=True)
        return Response({"virtances": serilizator.data})

    def post(self, request, *args, **kwargs):
        serilizator = CreateVirtanceSerializer(data=request.data, context={'request': request})
        serilizator.is_valid(raise_exception=True)
        validated_data = serilizator.save(password=request.data.get("password"))
        virtance = Virtance.objects.get(pk=validated_data.get("id"))
        serilizator = self.class_serializer(virtance, many=False)
        return Response({"virtance": serilizator.data}, status=status.HTTP_201_CREATED)


class VirtanceDataAPI(APIView):
    class_serializer = VirtanceSerializer

    def get_object(self):
        return get_object_or_404(
            Virtance, pk=self.kwargs.get("id"), user=self.request.user, is_deleted=False
        )

    def get(self, request, *args, **kwargs):
        virtances = self.get_object()
        serilizator = self.class_serializer(virtances, many=False)
        return Response({"virtance": serilizator.data})

    def delete(self, request, *args, **kwargs):
        virtance = self.get_object()
        delete_virtance.delay(virtance.id)
        return Response(status=status.HTTP_204_NO_CONTENT)


class VirtanceActionAPI(APIView):
    class_serializer = VirtanceActionSerializer

    def get_object(self):
        return get_object_or_404(
            Virtance, pk=self.kwargs.get("id"), user=self.request.user, is_deleted=False
        )

    def post(self, request, *args, **kwargs):
        virtance = self.get_object()
        serilizator = self.class_serializer(data=request.data)
        serilizator.is_valid(raise_exception=True)
        serilizator.save(virtance=virtance)
        return Response(serilizator.data)


class VirtanceConsoleAPI(APIView):
    def get_object(self):
        return get_object_or_404(
            Virtance, pk=self.kwargs.get("id"), user=self.request.user, is_deleted=False
        )

    def get(self, request, *args, **kwargs):
        virtance = self.get_object()
        wvcomp = WebVirtCompute(virtance.compute.token, virtance.compute.hostname)
        res = wvcomp.get_virtance_vnc(virtance.id)
        vnc_password = res.get("vnc_password")
        console_host = settings.WEBSOCKET_HOST
        console_port = 6080 if console_host == "localhost" else console_port
        response = Response(
            {
                "console": {
                    "id": virtance.id,
                    "name": virtance.name,
                    "websocket": {
                        "host": console_host,
                        "port": console_port,
                        "hash": make_vnc_hash(vnc_password),
                    },
                }
            }
        )
        response.set_cookie(
            "uuid",
            virtance.uuid,
            secure=True,
            httponly=True
        )
        return response


class VirtanceMetricsCpuAPI(APIView):
    def get_object(self):
        return get_object_or_404(
            Virtance, pk=self.kwargs.get("id"), user=self.request.user, is_deleted=False
        )

    def get(self, request, *args, **kwargs):
        virtance = self.get_object()
        vname = f"{settings.VM_NAME_PREFIX}{str(virtance.id)}"
        today = timezone.now()
        timestamp_today = time.mktime(today.timetuple())
        timestamp_yesterday = time.mktime((today - timezone.timedelta(days=1)).timetuple())
        
        cpu_sys_query = (
            f"(irate(libvirt_domain_info_cpu_time_system{{domain='{vname}'}}[5m])*100)/on(domain)"
            f"(count(libvirt_domain_info_vcpu_state{{domain='{vname}'}})by(domain)*1000000000)"
        )
        cpu_usr_query = (
            f'(irate(libvirt_domain_info_cpu_time_total{{domain="{vname}"}}[5m])*100)/on(domain)'
            f'(count(libvirt_domain_info_vcpu_state{{domain="{vname}"}})by(domain)*1000000000)'
        )

        wvcomp = WebVirtCompute(virtance.compute.token, virtance.compute.hostname)
        cpu_sys_res = wvcomp.get_metrics(cpu_sys_query, timestamp_yesterday, timestamp_today, 300)
        cpu_usr_res = wvcomp.get_metrics(cpu_usr_query, timestamp_yesterday, timestamp_today, 300)

        try:
            sys_value = cpu_sys_res['data']['result'][0]['values']
        except KeyError:
            sys_value = []

        try:
            user_value = cpu_usr_res['data']['result'][0]['values']
        except KeyError:
            user_value = []


        data = {
            "sys": sys_value, 
            "user": user_value
        }
        return Response({"metrics": {"name": "CPU", "unit": "%", "data": data}})
