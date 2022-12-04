from base64 import b64decode, binascii
from rest_framework import serializers

from .models import KeyPair


class KeyPairSerializer(serializers.ModelSerializer):
    name = serializers.CharField(max_length=255)
    public_key = serializers.CharField(max_length=1000)
    fingerprint = serializers.CharField(read_only=True)

    class Meta:
        model = KeyPair
        fields = (
            "id",
            "name",
            "public_key",
            "fingerprint",
        )

    def validate_public_key(self, value):
        if not value.startswith("ssh-rsa"):
            raise serializers.ValidationError("Invalid public key format.")
        if len(value.strip().split()) != 2:
            raise serializers.ValidationError("Invalid public key format.")
        try:
            b64decode(value.strip().split()[1])
        except (TypeError, binascii.Error):
            raise serializers.ValidationError("Invalid public key format.")
        
        try:
            KeyPair.objects.get(public_key=value)
            raise serializers.ValidationError("Key already exists.")
        except KeyPair.DoesNotExist:
            pass

        return value

    def update(self, instance, validated_data):
        try:
            KeyPair.objects.get(public_key=validated_data.get("public_key"))
            raise serializers.ValidationError("Key already exists.")
        except KeyPair.DoesNotExist:
            pass
        instance.name = validated_data.get("name", instance.name)
        instance.public_key = validated_data.get("public_key", instance.public_key)
        instance.save()
        return instance

    def create(self, validated_data):
        return KeyPair.objects.create(**validated_data)
