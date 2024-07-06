from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from django.shortcuts import get_object_or_404

from webvirtcloud.views import error_message_response
from .models import LBaaS
from .serializers import LBaaSSerializer


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

    def get(self, request, *args, **kwargs):
        serializer = self.class_serializer(self.get_object(), many=False)
        return Response({"load_balancer": serializer.data})

    def delete(self, request, *args, **kwargs):
        lbaas = self.get_object()
        return Response(status=status.HTTP_204_NO_CONTENT)


class LBaaSVirtancesAPI(APIView):
    class_serializer = LBaaSSerializer

    def get_object(self):
        return get_object_or_404(LBaaS, uuid=self.kwargs.get("uuid"), user=self.request.user, is_deleted=False)

    def post(self, request, *args, **kwargs):
        lbaas = self.get_object()

        if lbaas.event is not None:
            return error_message_response("The load balancer already has event.")

        serializer = self.class_serializer(lbaas, many=False)
        return Response({"load_balancer": serializer.data})

    def delete(self, request, *args, **kwargs):
        lbaas = self.get_object()

        if lbaas.event is not None:
            return error_message_response("The load balancer already has event.")

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
