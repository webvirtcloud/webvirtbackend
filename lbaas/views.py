from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response

from .models import LBaaS
from .serializers import LBaaSSerializer


class LBaaSListAPI(APIView):
    class_serializer = LBaaSSerializer

    def get_queryset(self):
        queryset = LBaaS.objects.filter(user=self.request.user, is_deleted=False)
        return queryset

    def get(self, request, *args, **kwargs):
        serilizator = self.class_serializer(self.get_queryset(), many=True)
        return Response({"load_balancers": serilizator.data})

    def post(self, request, *args, **kwargs):
        serializer = self.class_serializer(data=request.data, context={"user": request.user})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"load_balancer": serializer.data}, status=status.HTTP_201_CREATED)
