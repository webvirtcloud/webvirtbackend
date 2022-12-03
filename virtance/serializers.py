from decimal import Decimal
from rest_framework import serializers

from .models import Virtance
from size.serializers import SizeSerializer
from image.serializers import ImageSerializer
from region.serializers import RegionSerializer


class VirtanceSerializer(serializers.ModelSerializer):
    size = SizeSerializer()
    image = ImageSerializer()
    region = RegionSerializer()
    vcpu = serializers.IntegerField(source="size.vcpu")
    memory = serializers.IntegerField(source="size.memory")
    locked = serializers.BooleanField(source="is_locked")
    created_at = serializers.DateTimeField(source="created")
    disk = serializers.SerializerMethodField()
    status = serializers.SerializerMethodField()
    features = serializers.SerializerMethodField()
    networks = serializers.SerializerMethodField()
    backup_ids = serializers.SerializerMethodField()
    snapshot_ids = serializers.SerializerMethodField()

    class Meta:
        model = Virtance
        fields = (
            "id",
            "name",
            "vcpu",
            "memory",
            "disk",
            "locked",
            "status",
            "created_at",
            "features",
            "backup_ids",
            "snapshot_ids",
            "image",
            "size",
            "networks",
            "region",
        )

    def get_status(self, obj):
        return obj.INACTIVE

    def get_disk(self, obj):
        return self.obj.disk // (1024 ** 3)

    def get_features(self, obj):
        return []

    def get_backup_ids(self, obj):
        return []

    def get_snapshot_ids(self, obj):
        return []

    def create(self, validated_data):
        print(validated_data)
        return {**validated_data}

    def update(self, instance, validated_data):
        return instance


class CreateVirtanceSerializer(serializers.Serializer):
    size = serializers.SlugField()
    image = serializers.IntegerField()
    region = serializers.SlugField()
    name = serializers.CharField(max_length=100)

    def validate_name(self, value):
        raise serializers.ValidationError("Name already exists")
        return value

    def create(self, validated_data):
        return {**validated_data}

    def update(self, instance, validated_data):
        return instance
