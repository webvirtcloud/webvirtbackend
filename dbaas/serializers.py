from django.conf import settings
from rest_framework import serializers

from image.models import Image
from region.models import Region
from size.models import DBMS, Size
from virtance.models import Virtance
from network.models import Network, IPAddress
from size.serializers import SizeSerializer
from region.serializers import RegionSerializer
from virtance.utils import encrypt_data, decrypt_data, make_passwd, make_ssh_private

from .models import DBaaS
from .tasks import create_dbaas


class DBaaSSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(required=False, read_only=True, source="uuid")
    name = serializers.CharField()
    size = serializers.CharField(write_only=True)
    event = serializers.SerializerMethodField(read_only=True)
    engine = serializers.CharField(write_only=True)
    region = serializers.CharField(required=True, write_only=True)
    version = serializers.CharField(source="db.version", read_only=True)
    conection = serializers.SerializerMethodField(read_only=True)
    created_at = serializers.DateTimeField(read_only=True, source="created")

    class Meta:
        model = DBaaS
        fields = (
            "id",
            "name",
            "size",
            "event",
            "engine",
            "region",
            "version",
            "conection",
            "created_at",
        )

    def get_event(self, obj):
        if obj.event is None:
            return None
        return {"name": obj.event, "description": next((i[1] for i in obj.EVENT_CHOICES if i[0] == obj.event))}

    def get_conection(self, obj):
        if obj.virtance is None:
            return None
        ipv4_public = IPAddress.objects.get(network__type=Network.PUBLIC, virtance=obj.virtance)
        ipv4_private = IPAddress.objects.get(network__type=Network.PRIVATE, virtance=obj.virtance)
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
            if check_region.features.filter(name="load_balancer").exists() is False:
                raise serializers.ValidationError({"region": ["Region does not support load balancer."]})
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
        data["region"] = RegionSerializer(instance.virtance.region).data
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
        enc_private_key = encrypt_data(make_ssh_private())
        enc_admin_secret = encrypt_data(make_passwd(length=16))
        enc_master_secret = encrypt_data(make_passwd(length=16))

        dbms = DBMS.objects.filter(slug=engine, is_deleted=False).first()
        size = Size.objects.filter(type=Size.VIRTANCE, is_deleted=False).first()
        region = Region.objects.get(slug=region_slug, is_deleted=False)
        template = Image.objects.filter(type=Image.DBAAS, is_deleted=False).first()

        virtance = Virtance.objects.create(
            name=name,
            user=user,
            size=size,
            type=Virtance.DBAAS,
            region=region,
            disk=size.disk,
            template=template,
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
