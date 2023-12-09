from rest_framework.views import APIView
from rest_framework.response import Response

from .serializers import BalanceSerilizer


class BalanceAPI(APIView):
    serializer_class = BalanceSerilizer

    def get(self, request, *args, **kwargs):
        serializer = self.serializer_class(request.user)
        return Response(serializer.data)


class InvoiceHistoryAPI(APIView):
    def get(self, request, *args, **kwargs):
        response = {
            "invoices": [
                {
                    "uuid": "00000000-0000-0000-0000-000000000000",
                    "date": "2020-01-01T00:00:00Z",
                    "amount": "0.00",
                    "status": "paid",
                    "download_url": "https://api.webvirt.cloud/v1/billing/invoice/1.pdf",
                }
            ]
        }
        return Response(response)
