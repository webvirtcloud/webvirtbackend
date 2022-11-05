from rest_framework import serializers
from django.contrib.auth import authenticate

from .models import User, Token


class AuthTokenSerializer(serializers.Serializer):
    email = serializers.EmailField(label="Email", write_only=True)
    password = serializers.CharField(
        label="Password", style={"input_type": "password"}, trim_whitespace=False, write_only=True
    )

    def validate(self, attrs):
        email = attrs.get("email")
        password = attrs.get("password")

        if email and password:
            user = authenticate(request=self.context.get("request"), username=email, password=password)

            if not user:
                msg = "Unable to log in with provided credentials."
                raise serializers.ValidationError(msg, code="authorization")
        else:
            msg = 'Must include "email" and "password".'
            raise serializers.ValidationError(msg, code="authorization")

        attrs["user"] = user
        return attrs


class RegisterSerializer(serializers.Serializer):
    email = serializers.EmailField(label="Email", write_only=True)
    password = serializers.CharField(
        label="Password", style={"input_type": "password"}, trim_whitespace=False, write_only=True
    )

    def validate_password(self, password):
        if password and len(password) < 8:
            raise serializers.ValidationError("Password must be at least 8 characters long.")
        return password

    def validate(self, attrs):
        email = attrs.get("email")

        try:
            User.objects.get(email=email)
            raise serializers.ValidationError("User with this email already exists.")
        except User.DoesNotExist:
            pass

        return attrs

    def create(self, validated_data):
        email = validated_data.get("email")
        password = validated_data.get("password")

        user = User.objects.create_user(email=email, password=password)
        token = Token.objects.create(user=user, scope=Token.WRITE_SCOPE, is_obtained=True, name="Obtained auth token")

        validated_data["token"] = token.key
        return validated_data


class ResetPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField(label="Email", write_only=True)

    def create(self, validated_data):
        email = validated_data.get("email")

        try:
            user = User.objects.get(email=email)
            user.update_hash()
        except User.DoesNotExist:
            pass

        return validated_data


class ResetPasswordHashSerializer(serializers.Serializer):
    password = serializers.CharField(
        label="Password", style={"input_type": "password"}, trim_whitespace=False, write_only=True
    )
    password_confirm = serializers.CharField(
        label="Password Confirm", style={"input_type": "password"}, trim_whitespace=False, write_only=True
    )

    def validate_password(self, attrs):
        if attrs and len(attrs) < 8:
            raise serializers.ValidationError("Password must be at least 8 characters long.")
        return attrs

    def validate(self, attrs):
        password = attrs.get("password")
        password_confirm = attrs.get("password_confirm")

        if password != password_confirm:
            raise serializers.ValidationError("Passwords do not match.")

        return attrs

    def update(self, instance, validated_data):
        password = validated_data.get("password")

        if instance is None:
            serializers.ValidationError("Hash is incorrect or your account is not activated")

        instance.set_password(password)
        instance.update_hash()

        token = Token.objects.get(is_obtained=True, user=instance)
        token.generate_key()

        return validated_data


class ProfileSerilizer(serializers.ModelSerializer):
    email = serializers.EmailField(read_only=True)
    first_name = serializers.CharField(required=False)
    last_name = serializers.CharField(required=False)
    created_at = serializers.DateTimeField(source='created', read_only=True)
    updated_at = serializers.DateTimeField(source='updated', read_only=True)
    verified = serializers.BooleanField(source='is_verified', read_only=True)
    email_verified = serializers.BooleanField(source='is_email_verified', read_only=True)

    class Meta:
        model = User
        fields = [
            "uuid", "email", "first_name", "last_name", "verified", "email_verified", "created_at", "updated_at"
        ]

    def update(self, instance, validated_data):
        first_name = validated_data.get("first_name")
        last_name = validated_data.get("last_name")

        if first_name:
            instance.first_name = first_name
        if last_name:
            instance.last_name = last_name

        instance.save()

        return instance
