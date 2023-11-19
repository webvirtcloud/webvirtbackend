from ipaddress import IPv4Network
from rest_framework import serializers

from .models import FloatIP, FloatIPCounter
from .tasks import assign_floating_ip, reassign_floating_ip, unassign_floating_ip
from network.helper import assign_free_ipv4_public
from network.models import IPAddress
from virtance.models import Virtance
from region.serializers import RegionSerializer
from virtance.serializers import VirtanceSerializer


class FloatIPSerializer(serializers.ModelSerializer):
    ip = serializers.CharField(source="ipaddress.address", read_only=True)
    event = serializers.SerializerMethodField(read_only=True)
    region = RegionSerializer(source="ipaddress.network.region", read_only=True)
    virtance = VirtanceSerializer(source="ipaddress.virtance", read_only=True)
    virtance_id = serializers.IntegerField(write_only=True)
    
    class Meta:
        model = FloatIP
        fields = (
            "ip",
            "event",
            "region",
            "virtance",
            "virtance_id"
        )

    def get_event(self, obj):
        if obj.event is None:
            return None
        return {"name": obj.event, "description": next((i[1] for i in obj.EVENT_CHOICES if i[0] == obj.event))}

    def validate(self, attrs):
        user = self.context["user"]
        virtance_id = attrs.get("virtance_id")

        try:
            virtance = Virtance.objects.get(id=virtance_id, user=user, is_deleted=False)
        except Virtance.DoesNotExist:
            raise serializers.ValidationError("Virtance ID does not exist")
        
        if virtance.region.features.filter(name="floating_ip").exists() is False:
            raise serializers.ValidationError("Floating IP is not supported in this region.")

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


class FloatIPActionSerializer(serializers.Serializer):
    action = serializers.CharField(max_length=30)
    virtance_id = serializers.IntegerField(required=False)

    def validate_action(self, value):
        actions = [
            "assign",
            "unassign",
        ]
        if value not in actions:
            raise serializers.ValidationError({"action": ["Invalid action."]})
        return value

    def validate(self, attrs):
        floatip = self.context.get("floatip")

        if attrs.get("action") == "unassign":
            if floatip.ipaddress.virtance is None:
                raise serializers.ValidationError("This floating IP is not assigned to a Virtance.")

        if attrs.get("action") == "assign":
            if floatip.ipaddress.virtance is not None:
                raise serializers.ValidationError("This floating IP is already assigned to a Virtance.")
            if attrs.get("virtance_id") is None:
                raise serializers.ValidationError({"virtance_id": ["This field is required."]})

        return attrs

    def create(self, validated_data):
        floatip = self.context.get("floatip")
        action = validated_data.get("action")
        virtance_id = validated_data.get("virtance_id")

        if action == "assign":
            virtance = Virtance.objects.get(id=virtance_id)
            floatip.event = FloatIP.ASSIGN
            floatip.save()

            virtance.event = Virtance.ASSIGN_FLOATING_IP
            virtance.save()

            if floatip.ipaddress.virtance is None:
                assign_floating_ip.delay(floatip.id, virtance.id)
            else:
                reassign_floating_ip.delay(floatip.id, virtance.id)
        
        if action == "unassign":
            floatip.event = FloatIP.UNASSIGN
            floatip.save()

            unassign_floating_ip.delay(floatip.id)

        return validated_data
