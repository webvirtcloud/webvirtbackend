from rest_framework import serializers
from django.contrib.auth import authenticate

from .models import User, Token


class AuthTokenSerializer(serializers.Serializer):
    email = serializers.EmailField(label="Email", write_only=True)
    password = serializers.CharField(
        label="Password", style={'input_type': 'password'}, trim_whitespace=False, write_only=True
    )

    def validate(self, attrs):
        email = attrs.get('email')
        password = attrs.get('password')

        if email and password:
            user = authenticate(request=self.context.get('request'), username=email, password=password)

            if not user:
                msg = 'Unable to log in with provided credentials.'
                raise serializers.ValidationError(msg, code='authorization')
        else:
            msg = 'Must include "email" and "password".'
            raise serializers.ValidationError(msg, code='authorization')

        attrs['user'] = user
        return attrs


class RegisterSerializer(serializers.Serializer):
    email = serializers.EmailField(required=False, write_only=True)
    password = serializers.CharField(required=False, write_only=True)

    def validate_password(self, password):
        if password and len(password) < 8:
            raise serializers.ValidationError('Password must be at least 8 characters long.')
        return password

    def validate(self, attrs):
        email = attrs.get('email')

        try:
            User.objects.get(email=email)
            raise serializers.ValidationError('User with this email already exists.')
        except User.DoesNotExist:
           pass
        
        return attrs

    def create(self, validated_data):
        email = validated_data.get('email')
        password = validated_data.get('password')

        user = User.objects.create_user(email=email, password=password)
        token = Token.objects.create(
            user=user, scope=Token.WRITE_SCOPE, is_obtained=True, name='Obtained auth token'
        )
        
        validated_data['token'] = token.key
        return validated_data
