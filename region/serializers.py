from rest_framework import serializers

from .models import Region


class RegionSerializer(serializers.ModelSerializer):
    available = serializers.BooleanField(source="is_active")
    features = serializers.SerializerMethodField()

    class Meta:
        model = Region
        fields = ("slug", "name", "available", "features")

    def get_features(self, obj):
        return []
