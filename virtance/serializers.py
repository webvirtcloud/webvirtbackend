from decimal import Decimal
from django.db.models import Q
from rest_framework import serializers

from .models import Virtance
from size.models import Size
from image.models import Image
from region.models import Region
from keypair.models import KeyPair
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
    id = serializers.IntegerField(required=False, read_only=True)
    name = serializers.CharField(max_length=100)
    size = serializers.SlugField()
    image = serializers.CharField()
    region = serializers.SlugField()
    ipv6 = serializers.BooleanField(required=False)
    backups = serializers.BooleanField(required=False)
    keypairs = serializers.ListField(required=False, allow_empty=True)
    user_data = serializers.CharField(required=False, allow_blank=True)

 
    def validate_size(self, value):
        try:
            size = Size.objects.get(slug=value, is_deleted=False)
            if size.is_active is False:
                raise serializers.ValidationError({"size": ["Size is not active."]})
        except Size.DoesNotExist:
            raise serializers.ValidationError({"size": ["Size not found."]})
        return value

    def validate_image(self, value):
        if value.isdigit():
            try:
                image = Image.objects.get(
                    Q(type=Image.SNAPSHOT) | Q(type=Image.BACKUP) | Q(type=Image.CUSTOM),
                    id=value, is_deleted=False
                )
            except Image.DoesNotExist:
                raise serializers.ValidationError({"image": ["Image not found."]})
        else:
            try:
                image = Image.objects.get(
                    Q(type=Image.DISTRIBUTION) | Q(type=Image.APPLICATION),
                    slug=value, is_deleted=False
                )
                if image.is_active is False:
                    raise serializers.ValidationError({"image": ["Image is not active."]})
            except Image.DoesNotExist:
                raise serializers.ValidationError({"image": ["Image not found."]})
        return value

    def validate_region(self, value):
        try:
            region = Region.objects.get(slug=value, is_deleted=False)
            if region.is_active is False:
                raise serializers.ValidationError({"region": ["Region is not active."]})
        except Region.DoesNotExist:
            raise serializers.ValidationError({"region": ["Region not found."]})
        return value

    def validate_keypairs(self, value):
        for k_id in value:
            try:
                KeyPair.objects.get(id=k_id, user=self.context.get("request").user)
            except KeyPair.DoesNotExist:
                raise serializers.ValidationError({"keypairs": ["Invalid keypair ID."]})
        return value
