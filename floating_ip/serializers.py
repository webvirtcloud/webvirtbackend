from ipaddress import IPv4Network
from rest_framework import serializers

from .models import FloatIP, FloatIPCounter
from .tasks import assign_floating_ip
from network.helper import assign_free_ipv4_public
from network.models import IPAddress
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
        virtance = Virtance.objects.get(id=virtance_id)
        floatip = FloatIP.objects.create(user=virtance.user, event=FloatIP.CREATE)

        virtance.event = Virtance.ASSIGN_FLOATING_IP
        virtance.save()

        ipaddress_id = assign_free_ipv4_public(virtance.id, is_float=True)
        if ipaddress_id:
            ipaddress = IPAddress.objects.get(id=ipaddress_id)
            ipv4_subnet = IPv4Network(f"{ipaddress.address}/{ipaddress.network.netmask}", strict=False)

            floatip.ipaddress = ipaddress
            floatip.cidr = f"{ipaddress.address}/{ipv4_subnet.prefixlen}"
            floatip.save()

            FloatIPCounter.objects.create(floatip=floatip, amount=0.0)

        assign_floating_ip.delay(floatip.id, virtance.id)
        
        return floatip
