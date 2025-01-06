from django.db.models import Q
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from django.shortcuts import get_object_or_404

from webvirtcloud.views import error_message_response
from virtance.models import Virtance
from virtance.serializers import VirtanceSerializer
from .models import LBaaS, LBaaSVirtance
from .tasks import delete_lbaas
from .serializers import (
    LBaaSSerializer,
    LBaaSUpdateSerializer,
    LBaaSAddRuleSerializer,
    LBaaSDelRuleSerializer,
    LBaaSUpdateRuleSerializer,
    LBaaSAddVirtanceSerializer,
    LBaaSDelVirtanceSerializer,
)


class LBaaSListAPI(APIView):
    class_serializer = LBaaSSerializer

    def get_queryset(self):
        return LBaaS.objects.filter(~Q(event=LBaaS.DELETE), user=self.request.user, is_deleted=False)

    def get(self, request, *args, **kwargs):
        """
        List All Load Balancers
        ---
        """
        serilizator = self.class_serializer(self.get_queryset(), many=True)
        return Response({"load_balancers": serilizator.data})

    def post(self, request, *args, **kwargs):
        """
        Create a New Load Balancer
        ---
            parameters:
                - name: name
                  description: Load Balancer Name
                  required: true
                  type: string

                - name: region
                  description: Region
                  required: true
                  type: string

                - name: virtance_ids
                  description: Virtances to be Attached to Load Balanced
                  required: true
                  type: array
                  items:
                    type: integer

                - name: redirect_http_to_https
                  description: Redirect HTTP to HTTPS
                  required: false
                  type: boolean

                - name: sticky_sessions
                  description: Sticky Session
                  required: false
                  type: object
                  properties:
                    cookie_ttl_seconds:
                      description: Cookie TTL
                      required: true
                      type: string
                    cookie_name:
                      description: Cookie Name
                      required: true
                      type: string

                - name: health_check
                  description: Health Check
                  required: true
                  type: object
                  properties:
                    protocol:
                      description: Protocol (HTTP or TCP)
                      required: true
                      type: string
                    port:
                      description: Port for Health Check
                      required: true
                      type: integer
                    path:
                      description: HTTP Path (required for HTTP only)
                      required: false
                      type: string
                    check_interval_seconds:
                      description: Interval
                      required: true
                      type: integer
                    response_timeout_seconds:
                      description: Check Timeout
                      required: true
                      type: integer
                    healthy_threshold:
                      description: Healthy Threshold
                      required: true
                      type: integer
                    unhealthy_threshold:
                      description: Unhealthy Threshold
                      required: true
                      type: integer

                - name: forwarding_rules
                  description: Forward Rules
                  required: true
                  type: array
                  items:
                    type: object
                    properties:
                      entry_port:
                        description: Entry Port (1-65535)
                        required: true
                        type: integer
                      entry_protocol:
                        description: Entry Protocol (TCP, UDP, HTTP, HTTPS, HTTP2 and HTTP3)
                        required: true
                        type: integer
                      target_port:
                        description: Target Port (1-65535)
                        required: true
                        type: integer
                      target_protocol:
                        description: Target Protocol (TCP, UDP, HTTP, HTTPS, HTTP2 and HTTP3)
                        required: true
                        type: integer
        """
        serializer = self.class_serializer(data=request.data, context={"user": request.user})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"load_balancer": serializer.data}, status=status.HTTP_201_CREATED)


class LBaaSDataAPI(APIView):
    class_serializer = LBaaSSerializer

    def get_object(self):
        return get_object_or_404(LBaaS, uuid=self.kwargs.get("uuid"), user=self.request.user, is_deleted=False)

    def put(self, request, *args, **kwargs):
        """
        Update The Existing Load Balancer
        ---
            parameters:
                - name: name
                  description: Load Balancer Name
                  required: true
                  type: string

                - name: redirect_http_to_https
                  description: Redirect HTTP to HTTPS
                  required: false
                  type: boolean

                - name: sticky_sessions
                  description: Empty object to disable '{}'
                  required: false
                  type: object
                  properties:
                    cookie_ttl_seconds:
                      description: Cookie TTL
                      required: true
                      type: string
                    cookie_name:
                      description: Cookie Name
                      required: true
                      type: string

                - name: health_check
                  description: Health Check
                  required: true
                  type: object
                  properties:
                    protocol:
                      description: Protocol (HTTP or TCP)
                      required: true
                      type: string
                    port:
                      description: Port for Health Check
                      required: true
                      type: integer
                    path:
                      description: HTTP Path (required for HTTP only)
                      required: false
                      type: string
                    check_interval_seconds:
                      description: Interval
                      required: true
                      type: integer
                    response_timeout_seconds:
                      description: Check Timeout
                      required: true
                      type: integer
                    healthy_threshold:
                      description: Healthy Threshold
                      required: true
                      type: integer
                    unhealthy_threshold:
                      description: Unhealthy Threshold
                      required: true
                      type: integer
        """
        lbaas = self.get_object()

        if lbaas.event is not None:
            return error_message_response("The load balancer already has event.")

        serializer = LBaaSUpdateSerializer(lbaas, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        serializer = self.class_serializer(lbaas, many=False)
        return Response({"load_balancer": serializer.data})

    def get(self, request, *args, **kwargs):
        """
        Retrieve Existing Load Balancer
        ---
        """
        serializer = self.class_serializer(self.get_object(), many=False)
        return Response({"load_balancer": serializer.data})

    def delete(self, request, *args, **kwargs):
        """
        Delete The Load Balancer
        ---
        """
        lbaas = self.get_object()

        if lbaas.event is not None:
            return error_message_response("The load balancer already has event.")

        lbaas.event = LBaaS.DELETE
        lbaas.save()

        delete_lbaas.delay(lbaas.id)
        return Response(status=status.HTTP_204_NO_CONTENT)


class LBaaSForwardRulesAPI(APIView):
    def get_object(self):
        return get_object_or_404(LBaaS, uuid=self.kwargs.get("uuid"), user=self.request.user, is_deleted=False)

    def post(self, request, *args, **kwargs):
        """
        Add Forward Rule to The Load Balancer
        ---
            parameters:
                name: forwarding_rules
                description: Forward Rules
                required: true
                type: array
                items:
                    type: object
                    properties:
                        entry_port:
                          description: Entry Port (1-65535)
                          required: true
                          type: integer

                        entry_protocol:
                          description: Entry Protocol (TCP, UDP, HTTP, HTTPS, HTTP2 and HTTP3)
                          required: true
                          type: integer

                        target_port:
                          description: Target Port (1-65535)
                          required: true
                          type: integer

                        target_protocol:
                          description: Target Protocol (TCP, UDP, HTTP, HTTPS, HTTP2 and HTTP3)
                          required: true
                          type: integer
        """
        lbaas = self.get_object()

        if lbaas.event is not None:
            return error_message_response("The load balancer already has event.")

        serializer = LBaaSAddRuleSerializer(lbaas, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    def put(self, request, *args, **kwargs):
        """
        Update Forward Rule to The Load Balancer
        ---
            parameters:
                name: forwarding_rules
                description: Forward Rules
                required: true
                type: array
                items:
                    type: object
                    properties:
                        entry_port:
                          description: Entry Port (1-65535)
                          required: true
                          type: integer

                        entry_protocol:
                          description: Entry Protocol (TCP, UDP, HTTP, HTTPS, HTTP2 and HTTP3)
                          required: true
                          type: integer

                        target_port:
                          description: Target Port (1-65535)
                          required: true
                          type: integer

                        target_protocol:
                          description: Target Protocol (TCP, UDP, HTTP, HTTPS, HTTP2 and HTTP3)
                          required: true
                          type: integer
        """
        lbaas = self.get_object()

        if lbaas.event is not None:
            return error_message_response("The load balancer already has event.")

        serializer = LBaaSUpdateRuleSerializer(lbaas, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    def delete(self, request, *args, **kwargs):
        """
        Delete Forward Rule from The Load Balancer
        ---
            parameters:
                name: forwarding_rules
                description: Forward Rules
                required: true
                type: array
                items:
                    type: object
                    properties:
                        entry_port:
                          description: Entry Port (1-65535)
                          required: true
                          type: integer

                        entry_protocol:
                          description: Entry Protocol (TCP, UDP, HTTP, HTTPS, HTTP2 and HTTP3)
                          required: true
                          type: integer

                        target_port:
                          description: Target Port (1-65535)
                          required: true
                          type: integer

                        target_protocol:
                          description: Target Protocol (TCP, UDP, HTTP, HTTPS, HTTP2 and HTTP3)
                          required: true
                          type: integer
        """
        lbaas = self.get_object()

        if lbaas.event is not None:
            return error_message_response("The load balancer already has event.")

        serializer = LBaaSDelRuleSerializer(lbaas, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(status=status.HTTP_204_NO_CONTENT)


class LBaaSVirtancesAPI(APIView):
    def get_object(self):
        return get_object_or_404(LBaaS, uuid=self.kwargs.get("uuid"), user=self.request.user, is_deleted=False)

    def get(self, request, *args, **kwargs):
        """
        List All Virtances Attached to The Load Balancer
        ---
        """
        virtance_ids = LBaaSVirtance.objects.filter(
            lbaas=self.get_object(), virtance__is_deleted=False, is_deleted=False
        ).values_list("virtance_id", flat=True)
        virtances = Virtance.objects.filter(id__in=virtance_ids)
        serilizator = VirtanceSerializer(virtances, many=True)
        return Response({"virtances": serilizator.data})

    def post(self, request, *args, **kwargs):
        """
        Attach Virtance to The Load Balancer
        ---
            parameters:
                - name: virtance_ids
                  description: Virtance ID
                  required: true
                  type: array
                    items:
                        type: integer
        """
        lbaas = self.get_object()

        if lbaas.event is not None:
            return error_message_response("The load balancer already has event.")

        serializer = LBaaSAddVirtanceSerializer(lbaas, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    def delete(self, request, *args, **kwargs):
        """
        Detach Virtance from The Load Balancer
        ---
            parameters:
                - name: virtance_ids
                  description: Virtance ID
                  required: true
                  type: array
                    items:
                        type: integer
        """
        lbaas = self.get_object()

        if lbaas.event is not None:
            return error_message_response("The load balancer already has event.")

        serializer = LBaaSDelVirtanceSerializer(lbaas, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(status=status.HTTP_204_NO_CONTENT)
