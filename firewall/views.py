from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response

from .models import Firewall, FirewallVirtance
from .serializers import (
    FirewallSerializer, 
    FirewallAddRuleSerializer,
    FirewallDelRuleSerializer,
    FirewallAddVirtanceSerializer, 
    FirewallDelVirtanceSerializer
)


class FirewallListAPI(APIView):
    class_serializer = FirewallSerializer

    def get_queryset(self):
        virtance_id = self.request.query_params.get("virtance_id", None)
        queryset = Firewall.objects.filter(user=self.request.user, is_deleted=False)

        if virtance_id:
            firewallvirtance = FirewallVirtance.objects.filter(virtance_id=virtance_id).first()
            queryset = queryset.filter(id=firewallvirtance.firewall.id) if firewallvirtance else []

        return queryset

    def get(self, request, *args, **kwargs):
        serilizator = self.class_serializer(self.get_queryset(), many=True)
        return Response({"firewalls": serilizator.data})

    def post(self, request, *args, **kwargs):
        serializer = self.class_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(user=request.user)
        return Response({"firewall": serializer.data}, status=status.HTTP_201_CREATED)


class FirewallDataAPI(APIView):
    class_serializer = FirewallSerializer

    def get_object(self):
        return get_object_or_404(Firewall, uuid=self.kwargs.get("uuid"), user=self.request.user, is_deleted=False)

    def get(self, request, *args, **kwargs):
        firewall = self.get_object()
        serilizator = self.class_serializer(firewall, many=False)
        return Response({"firewall": serilizator.data})

    def delete(self, request, *args, **kwargs):
        firewall = self.get_object()
        firewall.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class FirewallRuleAPI(APIView):
    def get_object(self):
        return get_object_or_404(Firewall, uuid=self.kwargs.get("uuid"), user=self.request.user, is_deleted=False)

    def post(self, request, *args, **kwargs):
        serializer = FirewallAddRuleSerializer(self.get_object(), data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    def delete(self, request, *args, **kwargs):
        serializer = FirewallDelRuleSerializer(self.get_object(), data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(status=status.HTTP_204_NO_CONTENT)


class FirewallVirtanceAPI(APIView):
    def get_object(self):
        return get_object_or_404(Firewall, uuid=self.kwargs.get("uuid"), user=self.request.user, is_deleted=False)

    def post(self, request, *args, **kwargs):
        serializer = FirewallAddVirtanceSerializer(self.get_object(), data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    def delete(self, request, *args, **kwargs):
        serializer = FirewallDelVirtanceSerializer(self.get_object(), data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(status=status.HTTP_204_NO_CONTENT)
