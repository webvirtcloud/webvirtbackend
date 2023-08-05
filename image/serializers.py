from rest_framework import serializers

from .models import Image


class ImageSerializer(serializers.ModelSerializer):
    name = serializers.CharField(max_length=255, write_only=True)
    event = serializers.SerializerMethodField(required=False)
    status = serializers.SerializerMethodField(required=False)
    public = serializers.SerializerMethodField(required=False)
    regions = serializers.SerializerMethodField(required=False)
    distribution = serializers.SerializerMethodField(required=False)
    min_disk_size = serializers.SerializerMethodField(required=False)
    size_gigabytes = serializers.SerializerMethodField(required=False)
    created_at = serializers.DateTimeField(source="created", required=False)

    class Meta:
        model = Image
        fields = (
            "id",
            "slug",
            "name",
            "type",
            "event",
            "public",
            "regions",
            "created_at",
            "description",
            "distribution",
            "min_disk_size",
            "size_gigabytes",
            "status",
        )

    def get_regions(self, obj):
        return [region.slug for region in obj.regions.all()]

    def get_public(self, obj):
        if obj.type == obj.DISTRIBUTION or obj.type == obj.APPLICATION:
            return True
        return False

    def get_status(self, obj):
        if obj.is_active is True:
            return "available"
        return "unavailable"

    def get_event(self, obj):
        if obj.event is None:
            return None
        return {
            "name": obj.event,
            "description": next((i[1] for i in obj.EVENT_CHOICES if i[0] == obj.event))
        }

    def get_distribution(self, obj):
        for distro in obj.DISTRO_CHOICES:
            if distro[0] == obj.distribution:
                return distro[1]

    def get_min_disk_size(self, obj):
        if obj.type == obj.DISTRIBUTION or obj.type == obj.APPLICATION:
            return 0
        return obj.disk_size // 1073741824

    def get_size_gigabytes(self, obj):
        if obj.type == obj.DISTRIBUTION or obj.type == obj.APPLICATION:
            return 0
        return round(obj.file_size / 1073741824, 2)

    def validate(self, attrs):
        if attrs.get("name") is None:
            raise serializers.ValidationError({"name": ["This field is required."]})

        return attrs

    def update(self, instance, validated_data):
        instance.name = validated_data.get("name", instance.name)
        instance.save()
        return instance
