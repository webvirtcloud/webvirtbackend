from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response

from .models import FloatIP
from .serializers import FloatIPSerializer


class FloatingIPListAPI(APIView):
    class_serializer = FloatIPSerializer

    def get_queryset(self):
        return FloatIP.objects.filter(user=self.request.user)

    def get(self, request, *args, **kwargs):
        serializer = self.class_serializer(self.get_queryset(), many=True)
        return Response({"floating_ips": serializer.data})

    def post(self, request, *args, **kwargs):
        serializer = self.class_serializer(data=request.data, context={"user": request.user})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"floating_ips": serializer.data}, status=status.HTTP_201_CREATED)
  