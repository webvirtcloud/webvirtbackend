from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response

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
        serilizator.save()
        return Response({"virtance": serilizator.data}, status=status.HTTP_201_CREATED)
