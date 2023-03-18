from django.conf import settings
from django.shortcuts import get_object_or_404
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
        console_port = settings.WEBSOCKET_PORT
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
