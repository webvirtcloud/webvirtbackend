from rest_framework import serializers

from .models import DBaaS
from size.models import Size, DBMS
from image.models import Image
from region.models import Region
from virtance.models import Virtance
from .tasks import create_dbaas
from virtance.utils import make_ssh_private, encrypt_data, make_passwd


class DBaaSSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(required=False, read_only=True, source="uuid")
    name = serializers.CharField()
    size = serializers.CharField()
    event = serializers.SerializerMethodField(read_only=True)
    engine = serializers.CharField(source="dbms.engine", read_only=True)
    region = serializers.CharField(write_only=True)
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
