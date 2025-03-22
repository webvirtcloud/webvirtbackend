from rest_framework import serializers

from .models import DBaaS


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
