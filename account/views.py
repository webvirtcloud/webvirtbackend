from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework.authtoken.views import ObtainAuthToken

from webvirtcloud.views import custom_exception
from .models import User, Token
from .serializers import (
    RegisterSerializer, 
    AuthTokenSerializer,
    ResetPasswordSerializer, 
    ResetPasswordHashSerializer,
)


class Login(ObtainAuthToken):
    serializer_class = AuthTokenSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data.get('user')

        try:
            token = Token.objects.get(user=user, scope=Token.WRITE_SCOPE, is_obtained=True)
        except Token.DoesNotExist:
            token = Token.objects.create(
                user=user, scope=Token.WRITE_SCOPE, is_obtained=True, name='Obtained auth token'
            )

        return Response({'token': token.key})


class Register(APIView):
    permission_classes = (AllowAny,)
    serializer_class = RegisterSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.save()
        return Response(data.get('token'), status=status.HTTP_201_CREATED)


class ResetPassword(APIView):
    permission_classes = (AllowAny,)
    serializer_class = ResetPasswordSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response()


class ResetPasswordHash(APIView):
    permission_classes = (AllowAny,)
    serializer_class = ResetPasswordHashSerializer

    def post(self, request, hash, *args, **kwargs):
        try:
            user = User.objects.get(hash=hash, is_active=True)
        except User.DoesNotExist:
            return custom_exception('Check your email for the reset password link.')
        
        serializer = self.serializer_class(user, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response()


class VerifyEmail(APIView):
    permission_classes = (AllowAny,)

    def get(self, request, *args, **kwargs):
        try:
            user = User.objects.get(hash=kwargs['hash'], is_active=False)
            user.is_active = True
            user.save()
        except User.DoesNotExist:
            msg = "Hash is incorrect or your account is not activated"
            return Response({'message': msg}, status=400)

        return Response()
