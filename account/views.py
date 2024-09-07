from django.conf import settings
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.permissions import AllowAny, IsAuthenticated

from webvirtcloud.views import error_message_response
from project.models import Project
from .models import User, Token
from .tasks import email_confirm_register
from .serializers import (
    RegisterSerializer,
    AuthTokenSerializer,
    ResetPasswordSerializer,
    ResetPasswordHashSerializer,
)
from .serializers import (
    ProfileSerilizer,
    ChangePasswordSerializer,
)


class Login(ObtainAuthToken):
    serializer_class = AuthTokenSerializer

    def post(self, request, *args, **kwargs):
        """
        Obtain Auth Token For The User
        ---
            parameters:
                - name: username
                  description: Username
                  required: true
                  type: string

                - name: password
                  description: Password
                  required: true
                  type: string
        """
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data.get("user")

        try:
            token = Token.objects.get(user=user, scope=Token.WRITE_SCOPE, is_obtained=True)
        except Token.DoesNotExist:
            token = Token.objects.create(
                user=user, scope=Token.WRITE_SCOPE, is_obtained=True, name="Obtained auth token"
            )

        return Response({"token": token.key})


class Register(APIView):
    permission_classes = (AllowAny,)
    serializer_class = RegisterSerializer

    def post(self, request, *args, **kwargs):
        """
        Register a New User
        ---
            parameters:
                - name: email
                  description: Email
                  required: true
                  type: string

                - name: password
                  description: Password
                  required: true
                  type: string
        """
        if settings.REGISTRATION_ENABLED is False:
            return error_message_response("Sorry, registration is disabled.")
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.save()
        return Response({"token": data.get("token")}, status=status.HTTP_201_CREATED)


class ResetPassword(APIView):
    permission_classes = (AllowAny,)
    serializer_class = ResetPasswordSerializer

    def post(self, request, *args, **kwargs):
        """
        Reset the User Password
        ---
            parameters:
                - name: email
                  description: Email
                  required: true
                  type: string
        """
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response()


class ResetPasswordHash(APIView):
    permission_classes = (AllowAny,)
    serializer_class = ResetPasswordHashSerializer

    def post(self, request, hash, *args, **kwargs):
        """
        Reset he User Password by Hash
        ---
            parameters:
                - name: password
                  description: Password
                  required: true
                  type: string

                - name: password_confirm
                  description: Password confirm
                  required: true
                  type: string     
        """
        if User.objects.filter(hash=hash, is_active=True).exists():
            user = User.objects.get(hash=hash)
            serializer = self.serializer_class(user, data=request.data)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(status=status.HTTP_200_OK)
        return error_message_response("User not found or hash is invalid.")


class VerifyResendEmail(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request, *args, **kwargs):
        """
        Resend Vrification Email
        ---
        """
        if request.user.is_email_verified:
            return error_message_response("Account already verified.")
        request.user.update_hash()
        email_confirm_register.delay(request.user.email, request.user.hash)
        return Response(status=status.HTTP_200_OK)


class VerifyHashEmail(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request, *args, **kwargs):
        """
        Verify Email by Hash
        ---
        """
        if User.objects.filter(hash=kwargs.get("hash"), is_email_verified=False, is_active=True).exists():
            user = User.objects.get(hash=kwargs.get("hash"))
            user.email_verify()
            if settings.VERIFICATION_ENABLED is False:
                user.verify()
            user.update_hash()
            user_name = user.email.split("@")[0]
            project_name = f"{user_name.capitalize()}'s project"
            Project.objects.create(name=project_name, user=user, is_default=True)

            return Response(status=status.HTTP_200_OK)
        return error_message_response("Invalid token or email already verified.")


class ProfileAPI(APIView):
    serializer_class = ProfileSerilizer
    permission_classes = (IsAuthenticated,)

    def get(self, request, *args, **kwargs):
        """
        Retrieve THe User Profile
        ---
        """
        serializer = self.serializer_class(request.user)
        return Response({"profile": serializer.data})

    def put(self, request, *args, **kwargs):
        """
        Update The User Profile
        ---
            parameters: 
                - name: first_name
                  description: First name
                  required: false
                  type: string

                - name: last_name
                  description: Last name
                  required: false
                  type: string
        """
        serializer = self.serializer_class(request.user, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"profile": serializer.data})


class ChangePasswordAPI(APIView):
    serializer_class = ChangePasswordSerializer
    permission_classes = (IsAuthenticated,)

    def post(self, request, *args, **kwargs):
        """
        Change The User Password
        ---
            parameters:
                - name: old_password
                  description: Old password
                  required: true
                  type: string
                
                - name: new_password
                  description: New password
                  required: true
                  type: string

                - name: new_password_confirm
                  description: New password confirm
                  required: true
                  type: string
        """
        serializer = self.serializer_class(request.user, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(status=status.HTTP_200_OK)
