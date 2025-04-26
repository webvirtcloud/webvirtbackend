from django.db.models import Q
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from webvirtcloud.views import error_message_response

from .models import DBaaS
from .serializers import DBaaSSerializer, DBaaSActionSerializer
from .tasks import delete_dbaas


class DBaaSListAPI(APIView):
    class_serializer = DBaaSSerializer

    def get_queryset(self):
        return DBaaS.objects.filter(~Q(event=DBaaS.DELETE), user=self.request.user, is_deleted=False)

    def get(self, request, *args, **kwargs):
        """
        List All Database
        ---
        """
        serilizator = self.class_serializer(self.get_queryset(), many=True)
        return Response({"databases": serilizator.data})

    def post(self, request, *args, **kwargs):
        """
        Create a New Database
        ---
            parameters:
                - name: name
                  description: Database name
                  required: true
                  type: string

                - name: region
                  description: Region
                  required: true
                  type: string

                - name: engine
                  description: Engine
                  required: true
                  type: string

                - name: size
                  description: Size
                  required: true
                  type: string
        """
        serializer = self.class_serializer(data=request.data, context={"user": request.user})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"database": serializer.data}, status=status.HTTP_201_CREATED)


class DBaaSDataAPI(APIView):
    class_serializer = DBaaSSerializer

    def get_object(self):
        return get_object_or_404(DBaaS, uuid=self.kwargs.get("uuid"), user=self.request.user, is_deleted=False)

    def get(self, request, *args, **kwargs):
        """
        Get Existing Database
        ---
        """
        serializer = self.class_serializer(self.get_object(), many=False)
        return Response({"database": serializer.data})

    def post(self, request, *args, **kwargs):
        """
        Database Actions
        ---
            parameters:
                - name: action
                  description: Database action
                  required: true
                  type: string
                  action:
                    - reboot
                    - resize
                    - reboot
                    - rename
                    - restore
                    - snapshot
                    - shutdown
                    - power_on
                    - power_off
                    - power_cyrcle
                    - password_reset
                    - enable_backups
                    - disable_backups

                - name: size
                  description: For "resize" action
                  required: false
                  type: string

                - name: name
                  description: For "rename" and "snapshot" actions
                  required: false
                  type: string

                - name: image
                  description: For "restore" actions
                  required: false
                  type: string

                - name: password
                  description: For "password_reset" action
                  required: false
                  type: string
        """
        dbaas = self.get_object()

        if dbaas.event is not None:
            return error_message_response("The database already has event.")

        serializer = DBaaSActionSerializer(dbaas, data=request.data, context={"dbaas": dbaas})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    def delete(self, request, *args, **kwargs):
        """
        Delete The Database
        ---
        """
        dbaas = self.get_object()

        if dbaas.event is not None:
            return error_message_response("The database already has event.")

        dbaas.event = DBaaS.DELETE
        dbaas.save()

        delete_dbaas.delay(dbaas.id)
        return Response(status=status.HTTP_204_NO_CONTENT)
