from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework.authtoken.views import ObtainAuthToken

from .models import User, Token
from .serializers import AuthTokenSerializer


class Login(ObtainAuthToken):
    serializer_class = AuthTokenSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        
        try:
            token = Token.objects.get(user=user, scope=Token.WRITE_SCOPE, is_obtained=True)
        except Token.DoesNotExist:
            token = Token.objects.create(
                user=user, scope=Token.WRITE_SCOPE, is_obtained=True, name='Obtained auth token'
            )
        
        return Response({'token': token.key})


class Register(APIView):
    permission_classes = (AllowAny,)

    def post(self, request, *args, **kwargs):
        email = request.data.get('email')
        password = request.data.get('password')
        
        user = User.objects.create_user(email=email, password=password)

        token = Token.objects.create(
            user=user, scope=Token.WRITE_SCOPE, is_obtained=True, name='Obtained auth token'
        )
        
        return Response({'token': token.key})
