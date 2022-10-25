from rest_framework.authentication import TokenAuthentication as BaseTokenAuthentication

from .models import Token


class TokenAuthentication(BaseTokenAuthentication):
    model = Token
