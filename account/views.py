from rest_framework.response import Response
from rest_framework.authtoken.views import ObtainAuthToken as BaseObtainAuthToken

from .models import Token


class ObtainAuthToken(BaseObtainAuthToken):

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        token = Token.objects.filter(user=user).first()
        if token is None:
            token = Token.objects.create(user=user, name='API token')
        return Response({'token': token.key})
