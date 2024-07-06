from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from django.shortcuts import get_object_or_404

from webvirtcloud.views import error_message_response
from virtance.models import Virtance
from virtance.serializers import VirtanceSerializer
from .models import LBaaS, LBaaSVirtance
from .serializers import LBaaSSerializer, LBaaSAddVirtanceSerializer, LBaaSDelVirtanceSerializer
from .tasks import delete_lbaas


class LBaaSListAPI(APIView):
    class_serializer = LBaaSSerializer

    def get_queryset(self):
        queryset = LBaaS.objects.filter(user=self.request.user, is_deleted=False)
        return queryset

    def get(self, request, *args, **kwargs):
        serilizator = self.class_serializer(self.get_queryset(), many=True)
        return Response({"load_balancers": serilizator.data})

    def post(self, request, *args, **kwargs):
        serializer = self.class_serializer(data=request.data, context={"user": request.user})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"load_balancer": serializer.data}, status=status.HTTP_201_CREATED)


class LBaaSDataAPI(APIView):
    class_serializer = LBaaSSerializer

    def get_object(self):
        return get_object_or_404(LBaaS, uuid=self.kwargs.get("uuid"), user=self.request.user, is_deleted=False)

    def put(self, request, *args, **kwargs):
        serializer = self.class_serializer(self.get_object(), many=False)
        return Response({"load_balancer": serializer.data})

    def get(self, request, *args, **kwargs):
        serializer = self.class_serializer(self.get_object(), many=False)
        return Response({"load_balancer": serializer.data})

    def delete(self, request, *args, **kwargs):
        lbaas = self.get_object()

        if lbaas.event is not None:
            return error_message_response("The load balancer already has event.")

        delete_lbaas.delay(lbaas.id)
        return Response(status=status.HTTP_204_NO_CONTENT)


class LBaaSVirtancesAPI(APIView):
    class_serializer = LBaaSAddVirtanceSerializer

    def get_object(self):
        return get_object_or_404(LBaaS, uuid=self.kwargs.get("uuid"), user=self.request.user, is_deleted=False)

    def get(self, request, *args, **kwargs):
        virtance_ids = LBaaSVirtance.objects.filter(lbaas=self.get_object(), is_deleted=False).values_list("virtance_id", flat=True)
        virtances = Virtance.objects.filter(id__in=virtance_ids)
        serilizator = VirtanceSerializer(virtances, many=True)
        return Response({"virtances": serilizator.data})

    def post(self, request, *args, **kwargs):
        lbaas = self.get_object()

        if lbaas.event is not None:
            return error_message_response("The load balancer already has event.")

        serializer = LBaaSAddVirtanceSerializer(self.get_object(), data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    def delete(self, request, *args, **kwargs):
        lbaas = self.get_object()

        if lbaas.event is not None:
            return error_message_response("The load balancer already has event.")
        
        serializer = LBaaSDelVirtanceSerializer(self.get_object(), data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(status=status.HTTP_204_NO_CONTENT)


class LBaaSForwardRulesAPI(APIView):
    class_serializer = LBaaSSerializer

    def get_object(self):
        return get_object_or_404(LBaaS, uuid=self.kwargs.get("uuid"), user=self.request.user, is_deleted=False)

    def post(self, request, *args, **kwargs):
        lbaas = self.get_object()

        if lbaas.event is not None:
            return error_message_response("The load balancer already has event.")

        serializer = self.class_serializer(self.get_object(), many=False)
        return Response({"load_balancer": serializer.data})

    def delete(self, request, *args, **kwargs):
        lbaas = self.get_object()

        if lbaas.event is not None:
            return error_message_response("The load balancer already has event.")

        return Response(status=status.HTTP_204_NO_CONTENT)
