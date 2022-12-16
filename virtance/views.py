from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response

from image.models import Image
from keypair.models import KeyPairVirtance
from .tasks import create_virtance
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
        validated_data = serilizator.validated_data
        ipv6 = validated_data.get("ipv6")
        name = validated_data.get("name")
        size = validated_data.get("size")
        region = validated_data.get("region")
        backups = validated_data.get("backups")
        password = validated_data.get("password")a
        keypairs = validated_data.get("keypairs")
        user_data = validated_data.get("user_data")

        if validated_data.get("size").isdigit():
            image = Image.objects.get(id=validated_data.get("image"))
        else:
            image = Image.objects.get(slug=validated_data.get("image"))

        virtance = Virtance.objects.create(
            user=request.user,
            name=name,
            disk=size.disk,
            size__slug=size,
            image=image,
            region__slug=region,
            user_data=user_data
        )

        if keypairs:
            for k_id in keypairs:
                KeyPairVirtance.objects.create(keypair_id=k_id, virtance=virtance)

        if ipv6:
            pass

        if backups:
           pass

        create_virtance.delay(virtance.id, password=password)

        serilizator = self.class_serializer(virtance, many=False)
        return Response({"virtance": serilizator.data}, status=status.HTTP_201_CREATED)
