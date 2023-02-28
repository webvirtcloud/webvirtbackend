from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response

from size.models import Size
from image.models import Image
from keypair.models import KeyPairVirtance
from .models import Virtance
from .serializers import VirtanceSerializer, CreateVirtanceSerializer


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
        try:
            return Virtance.objects.get(pk=self.kwargs.get("id"), user=self.request.user, is_deleted=False)
        except Virtance.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

    def get(self, request, *args, **kwargs):
        virtances = self.get_object()
        serilizator = self.class_serializer(virtances, many=False)
        return Response({"virtance": serilizator.data})
