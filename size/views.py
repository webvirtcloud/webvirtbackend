from rest_framework.views import APIView
from rest_framework.response import Response

from .models import Size, DBMS
from .serializers import SizeSerializer, DBMSSerializer


class SizeListAPI(APIView):
    class_serializer = SizeSerializer

    def get_queryset(self):
        return Size.objects.filter(type=Size.VIRTACE, is_deleted=False)

    def get(self, request, *args, **kwargs):
        """
        List All Sizes
        ---
        """
        serilizator = self.class_serializer(self.get_queryset(), many=True)
        return Response({"sizes": serilizator.data})


class DBMSListAPI(APIView):
    class_serializer = DBMSSerializer

    def get_queryset(self):
        return DBMS.objects.filter(is_deleted=False)

    def get(self, request, *args, **kwargs):
        """
        List All DBMS
        ---
        """
        serilizator = self.class_serializer(self.get_queryset(), many=True)
        return Response({"dbms": serilizator.data})
