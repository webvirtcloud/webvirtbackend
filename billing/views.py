from rest_framework.views import APIView
from rest_framework.response import Response

from .models import Billing
from .serializers import BillingSerializer


class BillingAPI(APIView):
    class_serializer = BillingSerializer

    def get_queryset(self):
        queryset = Billing.objects.filter(user=self.request.user).aggregate(balance=Sum("balance")) or 0
        return queryset

    def get(self, request, *args, **kwargs):
        serilizator = self.class_serializer(self.get_queryset(), many=True)
        return Response({"firewalls": serilizator.data})
