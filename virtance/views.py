from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response

from size.models import Size
from image.models import Image
from region.models import Region
from keypair.models import KeyPair, KeyPairVirtance
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
        region = validated_data.get("region")
        backups = validated_data.get("backups")
        keypairs = validated_data.get("keypairs")
        user_data = validated_data.get("user_data")
        user = self.context.get("request").user
        size = Size.objects.get(slug=validated_data.get("size"))
        image = Image.objects.get(slug=validated_data.get("image"))
        region = Region.objects.get(slug=validated_data.get("region"))

        virtance = Virtance.objects.create(
            user=user,
            name=name,
            disk=size.disk,
            size=size,
            image=image,
            region=region,
            user_data=user_data
        )

        if keypairs:
            for k_id in keypairs:
                keypair = KeyPair.objects.get(id=k_id)
                KeyPairVirtance.objects.create(keypair=keypair, virtance=virtance)

        if ipv6:
            pass

        if backups:
           pass

        serilizator = self.class_serializer(virtance, many=False)
        return Response({"virtance": serilizator.data}, status=status.HTTP_201_CREATED)
