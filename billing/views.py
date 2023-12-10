from rest_framework.views import APIView
from rest_framework.response import Response

from .models import Invoice
from .serializers import BalanceSerilizer, InvoiceSerializer


class BalanceAPI(APIView):
    serializer_class = BalanceSerilizer

    def get(self, request, *args, **kwargs):
        serializer = self.serializer_class(request.user)
        return Response(serializer.data)


class InvoiceListAPI(APIView):
    serializer_class = InvoiceSerializer

    def get(self, request, *args, **kwargs):
        invoices = Invoice.objects.filter(user=request.user)
        serializer = self.serializer_class(invoices, many=True)
        return Response({"invoices": serializer.data})


class InvoiceDataAPI(APIView):
    serializer_class = InvoiceSerializer

    def get_object(self):
        return get_object_or_404(Invoice, uuid=self.kwargs.get("uuid"), user=self.request.user)

    def get(self, request, *args, **kwargs):
        serializer = self.serializer_class(self.get_object(), many=False)
        return Response({"invoice": serializer.data})
