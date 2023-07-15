from django.db.models import Q
from django.http import Http404
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response

from .models import Image
from .tasks import image_delete
from .serializers import ImageSerializer


class ImageListAPI(APIView):
    class_serializer = ImageSerializer

    def get_queryset(self):
        user = self.request.user
        query_type = self.request.query_params.get("type", None)
        if query_type is None:
            queryset = Image.objects.filter(
                Q(type=Image.APPLICATION) | Q(type=Image.DISTRIBUTION) | 
                Q(type=Image.BACKUP, user=self.request.user) | 
                Q(type=Image.CUSTOM, user=self.request.user) |
                Q(type=Image.SNAPSHOT, user=self.request.user),
                is_deleted=False
            )
        else:
            if query_type == Image.DISTRIBUTION or query_type == Image.APPLICATION:
                user = None

            queryset = Image.objects.filter(type=query_type, user=user)
        return queryset

    def get(self, request, *args, **kwargs):
        serilizator = self.class_serializer(self.get_queryset(), many=True)
        return Response({"images": serilizator.data})


class ImageDataAPI(APIView):
    class_serializer = ImageSerializer

    def get_object(self):
        image = get_object_or_404(Image, pk=self.kwargs.get("id"), is_deleted=False)
        if image.type == Image.SNAPSHOT or image.type == Image.BACKUP or image.type == Image.CUSTOM:
            if image.user != self.request.user:
                raise Http404
        return image

    def get(self, request, *args, **kwargs):
        serilizator = self.class_serializer(self.get_object(), many=False)
        return Response({"image": serilizator.data})


    def delete(self, request, *args, **kwargs):
        image = self.get_object()
        if image.type != Image.CUSTOM or image.type != Image.SNAPSHOT:
            raise Http404
        image_delete.delay(image.id)
        return Response(status=status.HTTP_204_NO_CONTENT)
