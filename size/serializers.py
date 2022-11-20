from decimal import Decimal
from rest_framework import serializers

from .models import Size
from region.models import Region


class SizeSerializer(serializers.ModelSerializer):
    available = serializers.BooleanField(source="is_active")
    price_hourly = serializers.DecimalField(source='price', max_digits=10, decimal_places=6)
    price_monthly = serializers.SerializerMethodField()
    regions = serializers.SerializerMethodField()

    class Meta:
        model = Size
        fields = (
            "slug",
            "memory",
            "vcpu",
            "disk",
            "description",
            "available",
            "price_hourly",
            "price_monthly",
            "regions",
        )

    def get_price_monthly(self, obj):
        return int(round(obj.price * 730, 0))

    def get_regions(self, obj):
        return [region.slug for region in obj.regions.filter(is_deleted=False)]
