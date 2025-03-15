from django.db.models import Q
from rest_framework.views import APIView
from rest_framework.response import Response
from django.shortcuts import get_object_or_404

from .models import DBaaS
from .serializers import (
    DBaaSSerializer,
)


class DBaaSListAPI(APIView):
    class_serializer = DBaaSSerializer

    def get_queryset(self):
        return DBaaS.objects.filter(~Q(event=DBaaS.DELETE), user=self.request.user, is_deleted=False)

    def get(self, request, *args, **kwargs):
        """
        List All Database
        ---
        """
        serilizator = self.class_serializer(self.get_queryset(), many=True)
        return Response({"databases": serilizator.data})
