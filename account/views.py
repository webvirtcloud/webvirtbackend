from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework.authtoken.views import ObtainAuthToken

from .models import User, Token
from .serializers import AuthTokenSerializer, RegisterSerializer


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
    serializer_class = RegisterSerializer
    permission_classes = (AllowAny,)

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.save()
        return Response(data.get('token'), status=status.HTTP_201_CREATED)


class ResetPassword(APIView):
    permission_classes = (AllowAny,)

    def post(self, request, *args, **kwargs):
        email = request.data.get('email')

        return Response()


class ResetPasswordHash(APIView):
    permission_classes = (AllowAny,)

    def get(self, request, *args, **kwargs):
        try:
            User.objects.get(hash=kwargs['hash'], is_active=True)
        except User.DoesNotExist:
            msg = "Hash is incorrect or your account is not activated"
            return Response({'message': msg})

        return Response()

    def post(self, request, *args, **kwargs):
        password = request.data.get('password')
        password_confirm = request.data.get('password_confirm')

        try:
            user = User.objects.get(hash=kwargs['hash'], is_active=True)
            user.set_password(password)
            token = Token.objects.get(is_obtained=True, user=user)
            token.generate_key()
            token.save()
        except User.DoesNotExist:
            msg = "Hash is incorrect or your account is not activated"
            return Response({'message': msg}, status=400)

        return Response({'token': token.key})


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
