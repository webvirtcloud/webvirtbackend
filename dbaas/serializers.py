import re

from django.conf import settings
from django.db.models import Q
from rest_framework import serializers

from compute.webvirt import WebVirtCompute
from image.models import Image
from network.models import IPAddress, Network
from region.models import Region
from size.models import DBMS, Size
from size.serializers import SizeSerializer
from virtance.models import Virtance
from virtance.utils import decrypt_data, encrypt_data, make_passwd, make_ssh_private, virtance_error

from .models import DBaaS
from .tasks import (
    action_dbaas,
    backups_delete,
    create_dbaas,
    resize_dbaas,
    restore_dbaas,
    snapshot_dbaas,
    update_admin_password_dbaas,
)


class DBaaSSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(required=False, read_only=True, source="uuid")
    name = serializers.CharField()
    size = serializers.CharField(write_only=True)
    event = serializers.SerializerMethodField(read_only=True)
    engine = serializers.CharField(write_only=True)
    status = serializers.SerializerMethodField()
    region = serializers.CharField(required=True, write_only=True)
    version = serializers.CharField(source="db.version", read_only=True)
    conection = serializers.SerializerMethodField(read_only=True)
    created_at = serializers.DateTimeField(read_only=True, source="created")
    backups_enabled = serializers.BooleanField(required=False, source="virtance.is_backup_enabled")

    class Meta:
        model = DBaaS
        fields = (
            "id",
            "name",
            "size",
            "event",
            "engine",
            "status",
            "region",
            "version",
            "conection",
            "created_at",
            "backups_enabled",
        )

    def get_status(self, obj):
        if obj.event is not None:
            return obj.virtance.INACTIVE
        if not hasattr(self.root, "many"):
            obj.virtance.pending()
            if obj.virtance.event is None:
                if obj.virtance.compute is not None:
                    wvcomp = WebVirtCompute(obj.virtance.compute.token, obj.virtance.compute.hostname)
                    res = wvcomp.status_virtance(obj.virtance.id)
                    if res.get("detail"):
                        virtance_error(obj.virtance.id, res.get("detail"), event="status")
                    if res.get("status") == "running":
                        obj.virtance.active()
                    if res.get("status") == "shutoff":
                        obj.virtance.inactive()
        return obj.virtance.status

    def get_event(self, obj):
        if obj.event is None:
            return None
        return {"name": obj.event, "description": next((i[1] for i in obj.EVENT_CHOICES if i[0] == obj.event))}

    def get_conection(self, obj):
        if obj.virtance is None:
            return None
        ipv4_public = IPAddress.objects.filter(network__type=Network.PUBLIC, virtance=obj.virtance).first()
        ipv4_private = IPAddress.objects.filter(network__type=Network.PRIVATE, virtance=obj.virtance).first()
        if ipv4_public is None or ipv4_private is None:
            return None
        return {
            "public": {
                "uri": f"postgres://{settings.DBAAS_ADMIN_LOGIN}:{decrypt_data(obj.admin_secret)}"
                f"@{ipv4_public.address}:{settings.DBAAS_PGSQL_PORT}/{settings.DBAAS_DEFAULT_DB_NAME}?sslmode=disable",
                "host": ipv4_public.address,
            },
            "private": {
                "uri": f"postgres://{settings.DBAAS_ADMIN_LOGIN}:{decrypt_data(obj.admin_secret)}"
                f"@{ipv4_private.address}:{settings.DBAAS_PGSQL_PORT}/{settings.DBAAS_DEFAULT_DB_NAME}?sslmode=disable",
                "host": ipv4_private.address,
            },
            "user": settings.DBAAS_ADMIN_LOGIN,
            "password": decrypt_data(obj.admin_secret),
            "port": settings.DBAAS_PGSQL_PORT,
            "ssl": False,
        }

    def validate(self, attrs):
        size = attrs.get("size")
        engine = attrs.get("engine")
        region = attrs.get("region")

        # Check if region is active
        try:
            check_region = Region.objects.get(slug=region, is_deleted=False)
            if check_region.is_active is False:
                raise serializers.ValidationError({"region": ["Region is not active."]})
            if check_region.features.filter(name="database").exists() is False:
                raise serializers.ValidationError({"region": ["Region does not support database feature."]})
        except Region.DoesNotExist:
            raise serializers.ValidationError({"region": ["Region not found."]})

        # Check if size is active
        try:
            check_size = Size.objects.get(slug=size, is_deleted=False)
            if check_size.is_active is False:
                raise serializers.ValidationError({"size": ["Size is not active."]})
        except Size.DoesNotExist:
            raise serializers.ValidationError({"size": ["Size not found."]})

        # Check if engine is active
        try:
            check_engine = DBMS.objects.get(slug=engine, is_deleted=False)
            if check_engine.is_active is False:
                raise serializers.ValidationError({"engine": ["Engine is not active."]})
        except DBMS.DoesNotExist:
            raise serializers.ValidationError({"engine": ["Engine not found."]})

        # Check if engine is compatible with size
        if check_size not in check_engine.sizes.all():
            raise serializers.ValidationError({"size": ["Size not available for this engine"]})

        return attrs

    def to_representation(self, instance):
        data = super().to_representation(instance)

        data["size"] = SizeSerializer(instance.virtance.size).data
        data["region"] = {
            "slug": instance.virtance.region.slug,
            "name": instance.virtance.region.name,
            "sizes": [size.slug for size in instance.dbms.sizes.all()],
            "features": [feature.name for feature in instance.virtance.region.features.all()],
        }
        data["engine"] = {
            "slug": instance.dbms.slug,
            "name": instance.dbms.name,
            "version": instance.dbms.version,
        }
        return data

    def create(self, validated_data):
        user = self.context.get("user")
        name = validated_data.get("name")
        size = validated_data.get("size")
        engine = validated_data.get("engine")
        region_slug = validated_data.get("region")
        backups_enabled = validated_data.get("backups_enabled", False)
        enc_private_key = encrypt_data(make_ssh_private())
        enc_admin_secret = encrypt_data(make_passwd(length=16))
        enc_master_secret = encrypt_data(make_passwd(length=16))

        dbms = DBMS.objects.get(slug=engine, is_deleted=False)
        size = Size.objects.get(slug=size, type=Size.VIRTANCE, is_deleted=False)
        region = Region.objects.get(slug=region_slug, is_deleted=False)
        template = Image.objects.get(slug=settings.DBAAS_TEMPLATE_NAME, type=Image.DBAAS, is_deleted=False)

        virtance = Virtance.objects.create(
            name=name,
            user=user,
            size=size,
            type=Virtance.DBAAS,
            region=region,
            disk=size.disk,
            template=template,
            is_backup_enabled=backups_enabled,
        )

        dbass = DBaaS.objects.create(
            name=name,
            user=user,
            dbms=dbms,
            private_key=enc_private_key,
            virtance=virtance,
            admin_secret=enc_admin_secret,
            master_secret=enc_master_secret,
        )

        create_dbaas.delay(dbass.id)

        return dbass


class DBaaSActionSerializer(serializers.Serializer):
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
            "restore",
            "snapshot",
            "shutdown",
            "power_on",
            "power_off",
            "power_cyrcle",
            "password_reset",
            "enable_backups",
            "disable_backups",
        ]
        if value not in actions:
            raise serializers.ValidationError({"action": ["Invalid action."]})
        return value

    def validate(self, attrs):
        dbaas = self.context.get("dbaas")
        virtance = dbaas.virtance

        if attrs.get("action") == "resize":
            if virtance.region.features.filter(name="resize").exists() is False:
                raise serializers.ValidationError("Resizing is not supported in this region.")

            if attrs.get("size") is None:
                raise serializers.ValidationError({"size": ["This field is required."]})
            try:
                size = Size.objects.get(slug=attrs.get("size"))
            except Size.DoesNotExist:
                raise serializers.ValidationError({"size": ["Invalid size."]})

            if size not in dbaas.dbms.sizes.all():
                raise serializers.ValidationError({"size": ["Size not available for this engine"]})

            if size.is_active is False:
                raise serializers.ValidationError({"size": ["Size is not active."]})

            if virtance.region not in size.regions.all():
                raise serializers.ValidationError({"size": ["Size is not available in the region."]})

            if size.disk < virtance.size.disk or size.vcpu < virtance.size.vcpu or size.memory < virtance.size.memory:
                raise serializers.ValidationError({"size": ["New size is smaller than the current size."]})

        if attrs.get("action") == "rename":
            if attrs.get("name") is None:
                raise serializers.ValidationError({"name": ["This field is required."]})

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
                Image.objects.get(
                    Q(type=Image.SNAPSHOT) | Q(type=Image.BACKUP),
                    id=attrs.get("image"),
                    source=dbaas.virtance,
                    user=dbaas.user,
                )
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

        return attrs

    def create(self, validated_data):
        dbaas = self.context.get("dbaas")
        virtance = dbaas.virtance
        name = validated_data.get("name")
        size = validated_data.get("size")
        image = validated_data.get("image")
        action = validated_data.get("action")
        password = validated_data.get("password")

        # Set new task event
        dbaas.event = action
        dbaas.save()

        # Set new task event
        virtance.event = action
        virtance.status = virtance.PENDING
        virtance.save()

        if action in ["power_on", "power_off", "power_cyrcle", "shutdown", "reboot"]:
            action_dbaas.delay(dbaas.id, action)

        if action == "rename":
            dbaas.name = name
            dbaas.save()
            dbaas.reset_event()

        if action == "resize":
            size = Size.objects.get(slug=size)
            resize_dbaas.delay(dbaas.id, size.id)

        if action == "password_reset":
            if password is None:
                password = make_passwd(length=16)
            update_admin_password_dbaas.delay(dbaas.id, password)

        if action == "snapshot":
            snapshot_dbaas.delay(dbaas.id, name)

        if action == "restore":
            snapshot = Image.objects.get(id=image, source=dbaas.virtance)

            if snapshot.event is not None:
                raise serializers.ValidationError("The image already has event.")

            snapshot.event = Image.RESTORE
            snapshot.save()
            restore_dbaas.delay(dbaas.id, snapshot.id)

        if action == "enable_backups":
            virtance.enable_backups()
            virtance.active()
            virtance.reset_event()

        if action == "disable_backups":
            backups_delete.delay(dbaas.id)

        return validated_data
