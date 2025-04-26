from rest_framework import serializers

from size.models import Size

from .models import Region


class RegionSerializer(serializers.ModelSerializer):
    available = serializers.BooleanField(source="is_active")
    features = serializers.SerializerMethodField()
    sizes = serializers.SerializerMethodField()

    class Meta:
        model = Region
        fields = ("slug", "name", "available", "features", "sizes")

    def get_features(self, obj):
        return [obj.name for obj in obj.features.all()]

    def get_sizes(self, obj):
        return [size.slug for size in Size.objects.filter(is_deleted=False) if obj in size.regions.all()]
