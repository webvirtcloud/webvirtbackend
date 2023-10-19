from rest_framework import serializers

from .models import FloatIP
from .tasks import assign_floating_ip
from virtance.models import Virtance
from region.serializers import RegionSerializer
from virtance.serializers import VirtanceSerializer


class FloatIPSerializer(serializers.ModelSerializer):
    ip = serializers.CharField(source="ipaddress.address", read_only=True)
    region = RegionSerializer(source="ipaddress.network.region", read_only=True)
    virtance = VirtanceSerializer(source="ipaddress.virtance", read_only=True)
    virtance_id = serializers.IntegerField(write_only=True)
    
    class Meta:
        model = FloatIP
        fields = (
            "ip",
            "virtance",
            "region",
            "virtance_id"
        )

    def validate(self, attrs):
        user = self.context["user"]
        virtance_id = attrs.get("virtance_id")

        try:
            Virtance.objects.get(id=virtance_id, user=user, is_deleted=False)
        except Virtance.DoesNotExist:
            raise serializers.ValidationError("Virtance ID does not exist")

        try:
            FloatIP.objects.get(ipaddress__virtance_id=virtance_id, ipaddress__is_float=True)
            raise serializers.ValidationError("Virtance already has a floating IP")
        except FloatIP.DoesNotExist:
            pass

        return attrs

    def create(self, validated_data):
        virtance_id = validated_data.get("virtance_id")
        assign_floating_ip.delay(virtance_id)
        return FloatIP.objects.filter(ipaddress__virtance_id=virtance_id, ipaddress__is_float=True).first()
