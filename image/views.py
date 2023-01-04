from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response

from .models import Image
from .serializers import ImageSerializer


class ImageListAPI(APIView):
    class_serializer = ImageSerializer

    def get_queryset(self):
        image_type = self.request.query_params.get('type', None)
        images = Image.objects.filter(is_deleted=False)
        if image_type is not None:
            images = images.filter(type=image_type)
        return images

    def get(self, request, *args, **kwargs):
        serilizator = self.class_serializer(self.get_queryset(), many=True)
        return Response({"images": serilizator.data})
