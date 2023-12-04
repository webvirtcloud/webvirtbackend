from rest_framework import serializers

from .models import Billing


class ProfileSerilizer(serializers.ModelSerializer):
    balance = serializers.SerializerMethodField()

    class Meta:
        model = Billing
        fields = ["balance"]
