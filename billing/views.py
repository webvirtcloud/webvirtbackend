from django.db.models import Sum
from rest_framework.views import APIView
from rest_framework.response import Response

from .models import Balance


class BalanceAPI(APIView):
    def get(self, request, *args, **kwargs):
        balance = Balance.objects.filter(user=self.request.user).aggregate(balance=Sum("balance"))["balacne"] or 0
        response = {"account_balance": balance, "month_to_date_usage": "0.00"}
        return Response(response)


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
