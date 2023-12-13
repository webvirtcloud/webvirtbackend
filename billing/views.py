from weasyprint import HTML
from django.utils import timezone
from django.http import HttpResponse
from django.template.loader import get_template
from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework.response import Response

from image.models import SnapshotCounter
from virtance.models import VirtanceCounter
from floating_ip.models import FloatIPCounter
from .models import Balance, Invoice
from .serializers import BalanceSerilizer, BillingHistorySerilizer, InvoiceSerializer


class BalanceAPI(APIView):
    serializer_class = BalanceSerilizer

    def get(self, request, *args, **kwargs):
        serializer = self.serializer_class(request.user)
        return Response(serializer.data)


class BillingHistoryListAPI(APIView):
    serializer_class = BillingHistorySerilizer

    def get_object(self):
        return Balance.objects.filter(user=self.request.user)

    def get(self, request, *args, **kwargs):
        serializer = self.serializer_class(self.get_object(), many=True)
        return Response({"billing_history": serializer.data})


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


class InvoicePdfAPI(APIView):
    serializer_class = InvoiceSerializer

    def get_object(self):
        return get_object_or_404(Invoice, uuid=self.kwargs.get("uuid"), user=self.request.user)

    def get(self, request, *args, **kwargs):
        invoice = self.get_object()
        prev_month = invoice.create - timezone.timedelta(days=1)
        start_of_month = prev_month.replace(day=1, hour=0, minute=0, second=0)
        end_of_month = prev_month.replace(hour=23, minute=59, second=59, microsecond=999999)

        # Get virtance usage
        virtances = VirtanceCounter.objects.filter(
            virtance__user=invoice.user,
            started__gte=start_of_month,
            stopped__lte=end_of_month,
        )

        # Get snapshots usage
        snapshots = SnapshotCounter.objects.filter(
            image__user=invoice.user,
            started__gte=start_of_month,
            stopped__lte=end_of_month,
        )

        # Get floating ip usage
        floating_ips = FloatIPCounter.objects.filter(
            floatip__user=invoice.user,
            started__gte=start_of_month,
            stopped__lte=end_of_month,
        )

        context = {
            "invoice": invoice,
        }
        template = get_template('invoice_pdf.html')
        html_content = template.render(context)

        response = HttpResponse(content_type='application/pdf')
        response["Content-Disposition"] = f"attachment; filename='{invoice.uuid}.pdf'"
        HTML(string=html_content).write_pdf(response)
        return response
