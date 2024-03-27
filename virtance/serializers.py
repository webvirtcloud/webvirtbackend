import re
from django.db.models import Q
from rest_framework import serializers

from size.models import Size
from image.models import Image
from region.models import Region
from network.models import IPAddress
from keypair.models import KeyPair, KeyPairVirtance
from size.serializers import SizeSerializer
from image.serializers import ImageSerializer
from region.serializers import RegionSerializer
from compute.webvirt import WebVirtCompute
from .models import Virtance
from .utils import virtance_error
from .tasks import create_virtance, action_virtance, resize_virtance, reset_password_virtance, rebuild_virtance
from .tasks import enable_recovery_mode_virtance, disable_recovery_mode_virtance
from .tasks import backups_delete, snapshot_virtance, restore_virtance


class VirtanceSerializer(serializers.ModelSerializer):
    size = SizeSerializer()
    image = ImageSerializer(source="template")
    region = RegionSerializer()
    vcpu = serializers.IntegerField(source="size.vcpu")
    locked = serializers.BooleanField(source="is_locked")
    created_at = serializers.DateTimeField(source="created")
    recovery_mode = serializers.BooleanField(source="is_recovery_mode")
    backups_enabled = serializers.BooleanField(source="is_backup_enabled")
    disk = serializers.SerializerMethodField()
    event = serializers.SerializerMethodField()
    memory = serializers.SerializerMethodField()
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
            "size",
            "disk",
            "image",
            "event",
            "memory",
            "region",
            "locked",
            "status",
            "networks",
            "features",
            "created_at",
            "backup_ids",
            "snapshot_ids",
            "recovery_mode",
            "backups_enabled",
        )

    def get_status(self, obj):
        if not hasattr(self.root, "many"):
            obj.pending()
            if obj.event is None:
                if obj.compute is not None:
                    wvcomp = WebVirtCompute(obj.compute.token, obj.compute.hostname)
                    res = wvcomp.status_virtance(obj.id)
                    if res.get("detail"):
                        virtance_error(obj.id, res.get("detail"), event="status")
                    if res.get("status") == "running":
                        obj.active()
                    if res.get("status") == "shutoff":
                        obj.inactive()
        return obj.status

    def get_disk(self, obj):
        return obj.disk // 1073741824

    def get_event(self, obj):
        if obj.event is None:
            return None
        return {"name": obj.event, "description": next((i[1] for i in obj.EVENT_CHOICES if i[0] == obj.event))}

    def get_memory(self, obj):
        return obj.size.memory // 1048576

    def get_features(self, obj):
        return []

    def get_backup_ids(self, obj):
        return [image.id for image in Image.objects.filter(virtance=obj, type=Image.BACKUP, is_deleted=False)]

    def get_snapshot_ids(self, obj):
        return [image.id for image in Image.objects.filter(virtance=obj, type=Image.SNAPSHOT, is_deleted=False)]

    def get_networks(self, obj):
        v4 = []
        v6 = []
        for ip in IPAddress.objects.filter(virtance=obj, is_float=False):
            if ip.network.version == ip.network.IPv6:
                v6.append(
                    {
                        "address": ip.address,
                        "prefix": ip.network.netmask,
                        "gateway": ip.network.gateway,
                        "type": ip.network.type,
                    }
                )
            v4.append(
                {
                    "address": ip.address,
                    "netmask": ip.network.netmask,
                    "gateway": ip.network.gateway,
                    "type": ip.network.type,
                }
            )
        return {"v4": v4, "v6": v6}


class CreateVirtanceSerializer(serializers.Serializer):
    id = serializers.IntegerField(required=False, read_only=True)
    name = serializers.CharField(max_length=100)
    size = serializers.SlugField()
    image = serializers.CharField()
    region = serializers.SlugField()
    ipv6 = serializers.BooleanField(required=False)
    backups = serializers.BooleanField(required=False)
    password = serializers.CharField(required=False, allow_blank=True)
    keypairs = serializers.ListField(required=False, allow_empty=True)
    user_data = serializers.CharField(required=False, allow_blank=True)

    def validate(self, attrs):
        size = attrs.get("size")
        image = attrs.get("image")
        region = attrs.get("region")
        backups = attrs.get("backups")
        keypairs = attrs.get("keypairs")

        # Check if keypairs are active
        if keypairs:
            for k_id in keypairs:
                try:
                    KeyPair.objects.get(id=k_id, user=self.context.get("request").user)
                except KeyPair.DoesNotExist:
                    raise serializers.ValidationError({"keypairs": ["Invalid keypair ID."]})

        # Check if region is active
        try:
            check_region = Region.objects.get(slug=region, is_deleted=False)
            if check_region.is_active is False:
                raise serializers.ValidationError({"region": ["Region is not active."]})
            if backups is True and check_region.features.filter(name="backup").exists() is False:
                raise serializers.ValidationError({"region": ["Backups are not supported in this region."]})
        except Region.DoesNotExist:
            raise serializers.ValidationError({"region": ["Region not found."]})

        # Check if size is active
        try:
            check_size = Size.objects.get(slug=size, is_deleted=False)
            if check_size.is_active is False:
                raise serializers.ValidationError({"size": ["Size is not active."]})
        except Size.DoesNotExist:
            raise serializers.ValidationError({"size": ["Size not found."]})

        # Check if image is active
        if image.isdigit():
            try:
                check_image = Image.objects.get(
                    Q(type=Image.SNAPSHOT) | Q(type=Image.BACKUP) | Q(type=Image.CUSTOM), id=image, is_deleted=False
                )
            except Image.DoesNotExist:
                raise serializers.ValidationError({"image": ["Image not found."]})
        else:
            try:
                check_image = Image.objects.get(
                    Q(type=Image.DISTRIBUTION) | Q(type=Image.APPLICATION), slug=image, is_deleted=False
                )
                if check_image.is_active is False:
                    raise serializers.ValidationError({"image": ["Image is not active."]})
            except Image.DoesNotExist:
                raise serializers.ValidationError({"image": ["Image not found."]})

        # Check if size is available in region
        if check_region not in check_size.regions.all():
            raise serializers.ValidationError({"size": ["Size is not available in the region."]})

        # Check if image is available in region
        if check_region not in check_image.regions.all():
            raise serializers.ValidationError({"image": ["Image is not available in the region."]})

        # Check if image size is available in size
        if check_image.type == Image.SNAPSHOT or check_image.type == Image.BACKUP or check_image.type == Image.CUSTOM:
            if check_image.disk_size > check_size.disk:
                raise serializers.ValidationError({"image": ["Image disk size is bigger than size choosed."]})

        return attrs

    def create(self, validated_data):
        ipv6 = validated_data.get("ipv6")
        name = validated_data.get("name")
        user = self.context.get("request").user
        size_slug = validated_data.get("size")
        backups = validated_data.get("backups")
        password = validated_data.get("password")
        keypairs = validated_data.get("keypairs")
        region_slug = validated_data.get("region")
        user_data = validated_data.get("user_data")
        image_id_or_slug = validated_data.get("image")

        if image_id_or_slug.isdigit():
            template = Image.objects.get(id=image_id_or_slug)
        else:
            template = Image.objects.get(slug=image_id_or_slug)

        if template.type == Image.SNAPSHOT or template.type == Image.BACKUP:
            template.event = Image.RESTORE
            template.save()

        size = Size.objects.get(slug=size_slug)
        region = Region.objects.get(slug=region_slug)

        virtance = Virtance.objects.create(
            user=user,
            name=name,
            size=size,
            event=Virtance.CREATE,
            region=region,
            disk=size.disk,
            template=template,
            user_data=user_data,
        )

        if keypairs:
            for k_id in keypairs:
                KeyPairVirtance.objects.create(keypair_id=k_id, virtance=virtance)

        if ipv6:
            pass

        if backups:
            virtance.enable_backups()

        create_virtance.delay(virtance.id, password=password)

        validated_data["id"] = virtance.id
        return validated_data


class VirtanceActionSerializer(serializers.Serializer):
    size = serializers.SlugField(required=False)
    name = serializers.CharField(max_length=100, required=False)
    image = serializers.CharField(required=False)
    action = serializers.CharField(max_length=30)
    password = serializers.CharField(required=False)

    def validate_action(self, value):
        actions = [
            "reboot",
            "resize",
            "rename",
            "rebuild",
            "restore",
            "snapshot",
            "shutdown",
            "power_on",
            "power_off",
            "power_cyrcle",
            "password_reset",
            "enable_backups",
            "disable_backups",
            "enable_recovery_mode",
            "disable_recovery_mode",
        ]
        if value not in actions:
            raise serializers.ValidationError({"action": ["Invalid action."]})
        return value

    def validate(self, attrs):
        user = self.context.get("user")
        virtance = self.context.get("virtance")

        if attrs.get("action") == "resize":
            if virtance.region.features.filter(name="resize").exists() is False:
                raise serializers.ValidationError("Resizing is not supported in this region.")

            if attrs.get("size") is None:
                raise serializers.ValidationError({"size": ["This field is required."]})
            try:
                size = Size.objects.get(slug=attrs.get("size"))
            except Size.DoesNotExist:
                raise serializers.ValidationError({"size": ["Invalid size."]})

            if size.is_active is False:
                raise serializers.ValidationError({"size": ["Size is not active."]})

            if virtance.region not in size.regions.all():
                raise serializers.ValidationError({"size": ["Size is not available in the region."]})

            if size.disk < virtance.size.disk or size.vcpu < virtance.size.vcpu or size.memory < virtance.size.memory:
                raise serializers.ValidationError({"size": ["New size is smaller than the current size."]})

        if attrs.get("action") == "rename":
            if attrs.get("name") is None:
                raise serializers.ValidationError({"name": ["This field is required."]})

        if attrs.get("action") == "rebuild":
            if attrs.get("image") is None:
                raise serializers.ValidationError({"image": ["This field is required."]})
            try:
                Image.objects.get(Q(type=Image.DISTRIBUTION) | Q(type=Image.APPLICATION), slug=attrs.get("image"))
            except Image.DoesNotExist:
                raise serializers.ValidationError({"image": ["Image not found."]})

        if attrs.get("action") == "password_reset":
            if attrs.get("password"):
                if len(attrs.get("password")) == 8:
                    if not re.match(r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d).+$", attrs.get("password")):
                        raise serializers.ValidationError(
                            {
                                "password": [
                                    "Password must contain at least one uppercase letter, "
                                    "one lowercase letter and one digit."
                                ]
                            }
                        )

        if attrs.get("action") == "restore":
            if attrs.get("image") is None:
                raise serializers.ValidationError({"image": ["This field is required."]})
            try:
                Image.objects.get(Q(type=Image.SNAPSHOT) | Q(type=Image.BACKUP), id=attrs.get("image"), user=user)
            except Image.DoesNotExist:
                raise serializers.ValidationError({"image": ["Image not found."]})

        if attrs.get("action") == "snapshot":
            if virtance.region.features.filter(name="snapshot").exists() is False:
                raise serializers.ValidationError("Snapshots are not supported in this region.")
            if attrs.get("name") is None:
                raise serializers.ValidationError({"name": ["This field is required."]})

        if attrs.get("action") == "enable_backups":
            if virtance.region.features.filter(name="backup").exists() is False:
                raise serializers.ValidationError("Backups are not supported in this region.")
            if virtance.is_backup_enabled is True:
                raise serializers.ValidationError("Backups are already enabled.")

        if attrs.get("action") == "disable_backups":
            if virtance.is_backup_enabled is False:
                raise serializers.ValidationError("Backups are already disabled.")

        if attrs.get("action") == "enable_recovery_mode":
            if virtance.is_recovery_mode is True:
                raise serializers.ValidationError({"name": ["Recovey mode is already enabled."]})

        if attrs.get("action") == "disable_recovery_mode":
            if virtance.is_recovery_mode is False:
                raise serializers.ValidationError({"name": ["Recovey mode is already disabled."]})

        return attrs

    def create(self, validated_data):
        name = validated_data.get("name")
        size = validated_data.get("size")
        image = validated_data.get("image")
        action = validated_data.get("action")
        virtance = self.context.get("virtance")
        password = validated_data.get("password")

        # Set new task event
        virtance.event = action
        virtance.status = virtance.PENDING
        virtance.save()

        if action in ["power_on", "power_off", "power_cyrcle", "shutdown", "reboot"]:
            action_virtance.delay(virtance.id, action)

        if action == "rename":
            virtance.name = name
            virtance.save()
            virtance.reset_event()

        if action == "rebuild":
            image = Image.objects.get(slug=image)
            virtance.template = image
            virtance.save()
            rebuild_virtance.delay(virtance.id)

        if action == "resize":
            size = Size.objects.get(slug=size)
            resize_virtance.delay(virtance.id, size.id)

        if action == "password_reset":
            reset_password_virtance.delay(virtance.id, password)

        if action == "snapshot":
            snapshot_virtance.delay(virtance.id, name)

        if action == "restore":
            snapshot = Image.objects.get(id=image)

            if snapshot.event is not None:
                raise serializers.ValidationError("The image already has event.")

            snapshot.event = Image.RESTORE
            snapshot.save()
            restore_virtance.delay(virtance.id, snapshot.id)

        if action == "enable_recovery_mode":
            enable_recovery_mode_virtance.delay(virtance.id)

        if action == "disable_recovery_mode":
            disable_recovery_mode_virtance.delay(virtance.id)

        if action == "enable_backups":
            virtance.enable_backups()
            virtance.active()
            virtance.reset_event()

        if action == "disable_backups":
            backups_delete.delay(virtance.id)

        return validated_data


class VirtanceHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Virtance
        fields = (
            "id",
            "event",
            "created",
        )
