import time
from django.db.models import Q
from django.conf import settings
from django.utils import timezone
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response

from compute.webvirt import WebVirtCompute
from webvirtcloud.views import error_message_response
from firewall.serializers import FirewallSerializer
from image.serializers import ImageSerializer
from image.models import Image
from floating_ip.models import FloatIP
from lbaas.models import LBaaSVirtance
from firewall.models import FirewallVirtance
from .utils import make_vnc_hash, virtance_history
from .models import Virtance, VirtanceHistory
from .tasks import delete_virtance
from .serializers import (
    VirtanceSerializer,
    CreateVirtanceSerializer,
    VirtanceActionSerializer,
    VirtanceHistorySerializer,
)


class VirtanceListAPI(APIView):
    class_serializer = VirtanceSerializer

    def get_queryset(self):
        name = self.request.query_params.get("name")
        region = self.request.query_params.get("region")
        used_in_lb = self.request.query_params.get("used_in_lb")
        has_backups = self.request.query_params.get("has_backups")
        has_snapshots = self.request.query_params.get("has_snapshots")
        has_firewall = self.request.query_params.get("has_firewall")
        has_floating_ip = self.request.query_params.get("has_floating_ip")

        queryset = Virtance.objects.filter(
            ~Q(event=Virtance.DELETE), type=Virtance.VIRTANCE, user=self.request.user, is_deleted=False
        )

        if name:
            queryset = queryset.filter(name__icontains=name)
        if region:
            queryset = queryset.filter(region__slug=region)
        if has_backups == "true":
            queryset = queryset.filter(is_backup_enabled=True)
        if has_snapshots == "true":
            virtance_ids = Image.objects.filter(
                user=self.request.user, type=Image.SNAPSHOT, source__is_deleted=False, is_deleted=False
            ).values_list("source_id", flat=True)
            queryset = queryset.filter(id__in=virtance_ids)
        if used_in_lb == "true":
            virtance_ids = LBaaSVirtance.objects.filter(
                virtance__user=self.request.user, virtance__is_deleted=False, is_deleted=False
            ).values_list("virtance_id", flat=True)
            queryset = queryset.filter(id__in=virtance_ids)
        if used_in_lb == "false":
            virtance_ids = LBaaSVirtance.objects.filter(
                virtance__user=self.request.user, virtance__is_deleted=False, is_deleted=False
            ).values_list("virtance_id", flat=True)
            queryset = queryset.filter(~Q(id__in=virtance_ids))
        if has_firewall == "true":
            virtance_ids = FirewallVirtance.objects.filter(virtance__user=self.request.user).values_list(
                "virtance_id", flat=True
            )
            queryset = queryset.filter(id__in=virtance_ids)
        if has_firewall == "false":
            virtance_ids = FirewallVirtance.objects.filter(virtance__user=self.request.user).values_list(
                "virtance_id", flat=True
            )
            queryset = queryset.filter(~Q(id__in=virtance_ids))
        if has_floating_ip == "true":
            virtance_ids = FloatIP.objects.filter(
                ~Q(ipaddress__virtance=None), user=self.request.user, is_deleted=False
            ).values_list("ipaddress__virtance_id", flat=True)
            queryset = queryset.filter(id__in=virtance_ids)
        if has_floating_ip == "false":
            virtance_ids = FloatIP.objects.filter(
                ~Q(ipaddress__virtance=None), user=self.request.user, is_deleted=False
            ).values_list("ipaddress__virtance_id", flat=True)
            queryset = queryset.filter(~Q(id__in=virtance_ids))
        return queryset

    def get(self, request, *args, **kwargs):
        """
        List of All Virtances

        Search with netxt get parameters:
        ---
            parameters:
                - name: region
                  description: Region slug
                  required: false
                  type: string

                - name: name
                  description: Virtance name
                  required: false
                  type: string

                - name: used_in_lb
                  description: Used in Load Balancer
                  required: false
                  type: boolean

                - name: has_backups
                  description: Has backups
                  required: false
                  type: boolean

                - name: has_snapshots
                  description: Has snapshots
                  required: false
                  type: boolean

                - name: has_firewall
                  description: Has firewall
                  required: false
                  type: boolean

                - name: has_floating_ip
                  description: Has floating IP
                  required: false
                  type: boolean
        """
        serilizator = self.class_serializer(self.get_queryset(), many=True)
        return Response({"virtances": serilizator.data})

    def post(self, request, *args, **kwargs):
        """
        Create a New Virtance
        ---
            parameters:
                - name: name
                  description: Virtance name
                  required: true
                  type: string

                - name: region
                  description: Region slug
                  required: true
                  type: string

                - name: image
                  description: Slug size or ID for snapshot
                  required: true
                  type: string or integer

                - name: size
                  description: Slug size
                  required: true
                  type: integer

                - name: ipv6
                  description: Enable IPv6 (beta)
                  required: false
                  type: boolean

                - name: buckups
                  description: Enable automatic backups
                  required: false
                  type: boolean

                - name: password
                  description: Virtance password or skip for random
                  required: false
                  type: string

                - name: keypairs
                  description: SSH keypairs
                  required: false
                  type: array
                  items:
                    type: integer

                - name: user_data
                  description: User data
                  required: false
                  type: string
        """
        serilizator = CreateVirtanceSerializer(data=request.data, context={"request": request})
        serilizator.is_valid(raise_exception=True)
        validated_data = serilizator.save(password=request.data.get("password"))
        virtance = Virtance.objects.get(pk=validated_data.get("id"))
        serilizator = self.class_serializer(virtance, many=False)
        virtance_history(virtance.id, request.user.id, "virtance.create")
        return Response({"virtance": serilizator.data}, status=status.HTTP_201_CREATED)


class VirtanceDataAPI(APIView):
    class_serializer = VirtanceSerializer

    def get_object(self):
        return get_object_or_404(
            Virtance, pk=self.kwargs.get("id"), type=Virtance.VIRTANCE, user=self.request.user, is_deleted=False
        )

    def get(self, request, *args, **kwargs):
        """
        Retrieve an Existing Virtance
        ---
        """
        virtances = self.get_object()
        serilizator = self.class_serializer(virtances, many=False)
        return Response({"virtance": serilizator.data})

    def delete(self, request, *args, **kwargs):
        """
        Delete The Virtance
        ---
        """
        virtance = self.get_object()
        virtance.event = Virtance.DELETE
        virtance.save()
        delete_virtance.delay(virtance.id)
        virtance_history(virtance.id, request.user.id, "virtance.delete")
        return Response(status=status.HTTP_204_NO_CONTENT)


class VirtanceActionAPI(APIView):
    class_serializer = VirtanceActionSerializer

    def get_object(self):
        return get_object_or_404(
            Virtance, pk=self.kwargs.get("id"), type=Virtance.VIRTANCE, user=self.request.user, is_deleted=False
        )

    def post(self, request, *args, **kwargs):
        """
        Virtance Actions
        ---
            parameters:
                - name: action
                  description: Virtance action
                  required: true
                  type: string
                  action:
                    - reboot
                    - resize
                    - reboot
                    - rename
                    - rebuild
                    - restore
                    - snapshot
                    - shutdown
                    - power_on
                    - power_off
                    - power_cyrcle
                    - password_reset
                    - enable_backups
                    - disable_backups
                    - enable_recovery_mode
                    - disable_recovery_mode

                - name: size
                  description: For "resize" action
                  required: false
                  type: string

                - name: name
                  description: For "rename" and "snapshot" actions
                  required: false
                  type: string

                - name: image
                  description: For "restore" and "rebuild" actions
                  required: false
                  type: string

                - name: password
                  description: For "password_reset" action
                  required: false
                  type: string
        """
        virtance = self.get_object()

        if virtance.event is not None:
            return error_message_response("The virtance already has event.")

        serilizator = self.class_serializer(data=request.data, context={"user": request.user, "virtance": virtance})
        serilizator.is_valid(raise_exception=True)
        serilizator.save()
        virtance_history(virtance.id, request.user.id, f"virtance.{serilizator.data.get('action')}")
        return Response(serilizator.data)


class VirtanceBackupsAPI(APIView):
    class_serializer = ImageSerializer

    def get_objects(self):
        virtance = get_object_or_404(
            Virtance, pk=self.kwargs.get("id"), type=Virtance.VIRTANCE, user=self.request.user, is_deleted=False
        )
        return Image.objects.filter(type=Image.BACKUP, source_id=virtance.id, user=self.request.user, is_deleted=False)

    def get(self, request, *args, **kwargs):
        """
        List of The Virtance Backups
        ---
        """
        backups = self.get_objects()
        serilizator = self.class_serializer(backups, many=True)
        return Response({"backups": serilizator.data})


class VirtanceFirewallAPI(APIView):
    class_serializer = FirewallSerializer

    def get_object(self):
        virtance = get_object_or_404(
            Virtance, pk=self.kwargs.get("id"), type=Virtance.VIRTANCE, user=self.request.user, is_deleted=False
        )
        firewallinstance = FirewallVirtance.objects.filter(virtance=virtance).first()
        return firewallinstance.firewall if firewallinstance else None

    def get(self, request, *args, **kwargs):
        """
        Retrieve The Virtance Firewall
        ---
        """
        if not self.get_object():
            return Response({"firewall": None})
        serilizator = self.class_serializer(self.get_object(), many=False)
        return Response({"firewall": serilizator.data})


class VirtanceSnapshotsAPI(APIView):
    class_serializer = ImageSerializer

    def get_objects(self):
        virtance = get_object_or_404(
            Virtance, pk=self.kwargs.get("id"), type=Virtance.VIRTANCE, user=self.request.user, is_deleted=False
        )
        return Image.objects.filter(
            type=Image.SNAPSHOT, source_id=virtance.id, user=self.request.user, is_deleted=False
        )

    def get(self, request, *args, **kwargs):
        """
        List of The Virtance Snapshots
        ---
        """
        snapshots = self.get_objects()
        serilizator = self.class_serializer(snapshots, many=True)
        return Response({"snapshots": serilizator.data})


class VirtanceHistoryAPI(APIView):
    class_serializer = VirtanceHistorySerializer

    def get_object(self):
        return get_object_or_404(
            Virtance, pk=self.kwargs.get("id"), type=Virtance.VIRTANCE, user=self.request.user, is_deleted=False
        )

    def get(self, request, *args, **kwargs):
        """
        List of The Virtance History
        ---
        """
        virtance = self.get_object()
        virtance_history = VirtanceHistory.objects.filter(virtance=virtance)
        serilizator = self.class_serializer(virtance_history, many=True)
        return Response({"history": serilizator.data})


class VirtanceConsoleAPI(APIView):
    def get_object(self):
        return get_object_or_404(
            Virtance, pk=self.kwargs.get("id"), type=Virtance.VIRTANCE, user=self.request.user, is_deleted=False
        )

    def get(self, request, *args, **kwargs):
        """
        Show The Virtance Console
        ---
        """
        virtance = self.get_object()
        wvcomp = WebVirtCompute(virtance.compute.token, virtance.compute.hostname)
        res = wvcomp.get_virtance_vnc(virtance.id)
        console_host = settings.NOVNC_URL
        console_port = settings.NOVNC_PORT
        console_hash = make_vnc_hash(res.get("vnc_password"))
        virtance_history(virtance.id, request.user.id, "virtance.console")
        response = Response(
            {
                "console": {
                    "id": virtance.id,
                    "uuid": virtance.uuid,
                    "name": virtance.name,
                    "websocket": {
                        "host": console_host,
                        "port": console_port,
                        "hash": console_hash,
                    },
                }
            }
        )
        response.set_cookie("uuid", virtance.uuid, secure=True, httponly=True, domain=settings.SESSION_COOKIE_DOMAIN)
        return response


class VirtanceMetricsCpuAPI(APIView):
    def get_object(self):
        return get_object_or_404(
            Virtance, pk=self.kwargs.get("id"), type=Virtance.VIRTANCE, user=self.request.user, is_deleted=False
        )

    def get(self, request, *args, **kwargs):
        """
        Retrieve The Virtance CPU Metrics
        ---
        """
        virtance = self.get_object()
        vname = f"{settings.VM_NAME_PREFIX}{str(virtance.id)}"
        today = timezone.now()
        timestamp_today = time.mktime(today.timetuple())
        timestamp_yesterday = time.mktime((today - timezone.timedelta(days=1)).timetuple())

        cpu_usr_query = (
            f"(irate(libvirt_domain_info_cpu_time_user{{domain='{vname}'}}[5m])*100)/"
            f"(libvirt_domain_info_vcpu_num{{domain='{vname}'}}*1000000000)"
        )
        cpu_sys_query = (
            f"(irate(libvirt_domain_info_cpu_time_system{{domain='{vname}'}}[5m])*100)/"
            f"(libvirt_domain_info_vcpu_num{{domain='{vname}'}}*1000000000)"
        )
        cpu_total_query = (
            f"(irate(libvirt_domain_info_cpu_time{{domain='{vname}'}}[5m])*100)/"
            f"(libvirt_domain_info_vcpu_num{{domain='{vname}'}}*1000000000)"
        )

        wvcomp = WebVirtCompute(virtance.compute.token, virtance.compute.hostname)
        cpu_usr_res = wvcomp.get_metrics(cpu_usr_query, timestamp_yesterday, timestamp_today, "5m")
        cpu_sys_res = wvcomp.get_metrics(cpu_sys_query, timestamp_yesterday, timestamp_today, "5m")
        cpu_total_res = wvcomp.get_metrics(cpu_total_query, timestamp_yesterday, timestamp_today, "5m")

        try:
            user_value = cpu_usr_res["data"]["result"][0]["values"]
            for i, val in enumerate(user_value):
                if float(val[1]) > 100:
                    user_value[i][1] = str(100.0)
        except (KeyError, IndexError):
            user_value = []

        try:
            sys_value = cpu_sys_res["data"]["result"][0]["values"]
            for i, val in enumerate(sys_value):
                if float(val[1]) > 100:
                    sys_value[i][1] = str(100.0)
        except (KeyError, IndexError):
            sys_value = []

        try:
            total_value = cpu_total_res["data"]["result"][0]["values"]
            for i, val in enumerate(total_value):
                if float(val[1]) > 100:
                    total_value[i][1] = str(100.0)
        except (KeyError, IndexError):
            total_value = []

        data = {"sys": sys_value, "user": user_value, "total": total_value}
        return Response({"metrics": {"name": "CPU", "unit": "%", "data": data}})


class VirtanceMetricsMemAPI(APIView):
    def get_object(self):
        return get_object_or_404(
            Virtance, pk=self.kwargs.get("id"), type=Virtance.VIRTANCE, user=self.request.user, is_deleted=False
        )

    def get(self, request, *args, **kwargs):
        """
        Retrieve The Virtance Memory Metrics
        ---
        """
        virtance = self.get_object()
        vname = f"{settings.VM_NAME_PREFIX}{str(virtance.id)}"
        today = timezone.now()
        timestamp_today = time.mktime(today.timetuple())
        timestamp_yesterday = time.mktime((today - timezone.timedelta(days=1)).timetuple())

        mem_query = (
            f"(((avg_over_time(libvirt_domain_info_memory_actual{{domain='{vname}'}}[5m]))-"
            f"(avg_over_time(libvirt_domain_info_memory_unused{{domain='{vname}'}}[5m])))/"
            f"(avg_over_time(libvirt_domain_info_memory_actual{{domain='{vname}'}}[5m])))*100"
        )

        wvcomp = WebVirtCompute(virtance.compute.token, virtance.compute.hostname)
        mem_res = wvcomp.get_metrics(mem_query, timestamp_yesterday, timestamp_today, "5m")

        try:
            mem_value = mem_res["data"]["result"][0]["values"]
        except (KeyError, IndexError):
            mem_value = []

        data = mem_value
        return Response({"metrics": {"name": "Memory", "unit": "%", "data": data}})


class VirtanceMetricsNetAPI(APIView):
    def get_object(self):
        return get_object_or_404(
            Virtance, pk=self.kwargs.get("id"), type=Virtance.VIRTANCE, user=self.request.user, is_deleted=False
        )

    def get(self, request, *args, **kwargs):
        """
        Retrieve The Virtance Network Metrics
        ---
        """
        in_val = {}
        out_val = {}
        net_devs = [0, 1]
        virtance = self.get_object()
        vname = f"{settings.VM_NAME_PREFIX}{str(virtance.id)}"
        today = timezone.now()
        timestamp_today = time.mktime(today.timetuple())
        timestamp_yesterday = time.mktime((today - timezone.timedelta(days=1)).timetuple())

        rx_query = f"(irate(libvirt_domain_info_net_rx_bytes{{domain='{vname}'}}[5m])*8)/1048576"
        tx_query = f"(irate(libvirt_domain_info_net_tx_bytes{{domain='{vname}'}}[5m])*8)/1048576"

        wvcomp = WebVirtCompute(virtance.compute.token, virtance.compute.hostname)
        in_res = wvcomp.get_metrics(rx_query, timestamp_yesterday, timestamp_today, "5m")
        out_res = wvcomp.get_metrics(tx_query, timestamp_yesterday, timestamp_today, "5m")

        for dev in net_devs:
            try:
                in_val[dev] = in_res["data"]["result"][dev]["values"]
            except (KeyError, IndexError):
                in_val[dev] = []

            try:
                out_val[dev] = out_res["data"]["result"][dev]["values"]
            except (KeyError, IndexError):
                out_val[dev] = []

        return Response(
            {
                "metrics": [
                    {"name": "Pubic Network", "unit": "Mbps", "data": {"inbound": in_val[0], "outbound": in_val[0]}},
                    {
                        "name": "Private Network",
                        "unit": "Mbps",
                        "data": {"inbound": out_val[1], "outbound": out_val[1]},
                    },
                ]
            }
        )


class VirtanceMetricsDiskAPI(APIView):
    def get_object(self):
        return get_object_or_404(
            Virtance, pk=self.kwargs.get("id"), type=Virtance.VIRTANCE, user=self.request.user, is_deleted=False
        )

    def get(self, request, *args, **kwargs):
        """
        Retrieve The Virtance Disk Metrics
        ---
        """
        virtance = self.get_object()
        vname = f"{settings.VM_NAME_PREFIX}{str(virtance.id)}"
        today = timezone.now()
        timestamp_today = time.mktime(today.timetuple())
        timestamp_yesterday = time.mktime((today - timezone.timedelta(days=1)).timetuple())

        r_query = f"irate(libvirt_domain_info_block_read_bytes{{dev='vda',domain='{vname}'}}[5m])/1048576"
        w_query = f"irate(libvirt_domain_info_block_write_bytes{{dev='vda',domain='{vname}'}}[5m])/1048576"

        wvcomp = WebVirtCompute(virtance.compute.token, virtance.compute.hostname)
        rd_res = wvcomp.get_metrics(r_query, timestamp_yesterday, timestamp_today, "5m")
        wr_res = wvcomp.get_metrics(w_query, timestamp_yesterday, timestamp_today, "5m")

        try:
            rd_val = rd_res["data"]["result"][0]["values"]
        except (KeyError, IndexError):
            rd_val = []

        try:
            wr_val = wr_res["data"]["result"][0]["values"]
        except (KeyError, IndexError):
            wr_val = []

        return Response({"metrics": [{"name": "Disk", "unit": "MB/s", "data": {"read": rd_val, "write": wr_val}}]})
