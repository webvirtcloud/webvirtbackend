from rest_framework import serializers

from region.models import Region

from .models import Image


class ImageSerializer(serializers.ModelSerializer):
    name = serializers.CharField(max_length=255, required=False)
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
        return {"name": obj.event, "description": next((i[1] for i in obj.EVENT_CHOICES if i[0] == obj.event))}

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


class ImageActionSerializer(serializers.Serializer):
    action = serializers.CharField(max_length=30)
    region = serializers.CharField(max_length=30, required=False)

    def validate_action(self, value):
        actions = [
            "convert",
            "transfer",
        ]
        if value not in actions:
            raise serializers.ValidationError({"action": ["Invalid action."]})
        return value

    def validate(self, attrs):
        region = attrs.get("region")
        image = self.context.get("image")

        if attrs.get("action") == "convert":
            if image.type != Image.BACKUP:
                raise serializers.ValidationError({"action": ["Backup image can be converted only."]})

        if attrs.get("action") == "transfer":
            if image.type != Image.SNAPSHOT:
                raise serializers.ValidationError({"action": ["Snapshot image can be transferred only."]})

            # Check if region is active
            try:
                check_region = Region.objects.get(slug=region, is_deleted=False)
                if check_region.is_active is False:
                    raise serializers.ValidationError({"region": ["Region is not active."]})
                if check_region in image.regions.all():
                    raise serializers.ValidationError({"region": ["Image already transferred to the region."]})
            except Region.DoesNotExist:
                raise serializers.ValidationError({"region": ["Region not found."]})

            raise serializers.ValidationError({"image": ["Transfer action is not implemented yet."]})

        return attrs

    def create(self, validated_data):
        image = self.context.get("image")
        action = validated_data.get("action")

        # Set new task event
        image.event = action
        image.save()

        if action == Image.CONVERT:
            image.type = Image.SNAPSHOT
            image.name = f"{image.source.name}-{image.created.strftime('%Y-%m-%d %H:%M:%S')}"
            image.save()
            image.reset_event()

        if action == Image.TRANSFER:
            pass  # TODO: Transfer image to region

        return validated_data


class SnapshotsSerializer(serializers.ModelSerializer):
    name = serializers.CharField(max_length=255, required=False)
    event = serializers.SerializerMethodField(required=False)
    status = serializers.SerializerMethodField(required=False)
    public = serializers.SerializerMethodField(required=False)
    regions = serializers.SerializerMethodField(required=False)
    virtance_id = serializers.SerializerMethodField(required=False)
    distribution = serializers.SerializerMethodField(required=False)
    min_disk_size = serializers.SerializerMethodField(required=False)
    size_gigabytes = serializers.SerializerMethodField(required=False)
    created_at = serializers.DateTimeField(source="created", required=False)

    class Meta:
        model = Image
        fields = (
            "id",
            "name",
            "type",
            "event",
            "public",
            "regions",
            "created_at",
            "description",
            "virtance_id",
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
        return {"name": obj.event, "description": next((i[1] for i in obj.EVENT_CHOICES if i[0] == obj.event))}

    def get_virtance_id(self, obj):
        if obj.source.is_deleted is True:
            return None
        return obj.source.id

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
