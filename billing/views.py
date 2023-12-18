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
        virtance_list = []
        snapshot_list = []
        floating_ip_list = []
        invoice = self.get_object()
        prev_month = invoice.create - timezone.timedelta(days=1)
        start_of_month = prev_month.replace(day=1, hour=0, minute=0, second=0)
        end_of_month = prev_month.replace(hour=23, minute=59, second=59, microsecond=999999)

        # Get virtance usage
        virtances_counters = VirtanceCounter.objects.filter(
            virtance__user=invoice.user,
            started__gte=start_of_month,
            stopped__lte=end_of_month,
        )
        for virtance_count in virtances_counters:
            virtance_list.append(
                {
                    "name": f"{virtance_count.virtance.name} ({virtance_count.virtance.size.name})",
                    "start_at": virtance_count.started,
                    "stop_at": virtance_count.stopped,
                    "amount": virtance_count.amount,
                    "hour": (virtance_count.stopped - virtance_count.started).total_seconds() / 3600,
                }
            )
            if virtance_count.backup_amount > 0:
                virtance_list.append(
                    {
                        "name": f"{virtance_count.virtance.name} (Backup)",
                        "start_at": virtance_count.started,
                        "end_at": virtance_count.stopped,
                        "amount": virtance_count.backup_amount,
                        "hour": (virtance_count.stopped - virtance_count.started).total_seconds() / 3600,
                    }
                )
            if virtance_count.license_amount > 0:
                virtance_list.append(
                    {
                        "name": f"{virtance_count.virtance.name} (License)",
                        "start_at": virtance_count.started,
                        "stop_at": virtance_count.stopped,
                        "amount": virtance_count.license_amount,
                        "hour": (virtance_count.stopped - virtance_count.started).total_seconds() / 3600,
                    }
                )

        # Get snapshots usage
        snapshots_counters = SnapshotCounter.objects.filter(
            image__user=invoice.user,
            started__gte=start_of_month,
            stopped__lte=end_of_month,
        )
        for snapshot_count in snapshots_counters:
            snapshot_list.append(
                {
                    "name": f"{snapshot_count.image.name} ({snapshot_count.image.file_size / 1073741824}GB)",
                    "start_at": snapshot_count.started,
                    "stop_at": snapshot_count.stopped,
                    "amount": snapshot_count.amount,
                    "hour": (snapshot_count.stopped - snapshot_count.started).total_seconds() / 3600,
                }
            )

        # Get floating ip usage
        floating_ips_counters = FloatIPCounter.objects.filter(
            floatip__user=invoice.user,
            started__gte=start_of_month,
            stopped__lte=end_of_month,
        )
        for floating_ip_count in floating_ips_counters:
            floating_ip_list.append(
                {
                    "name": f"{floating_ip_count.ipaddress}",
                    "start_at": floating_ip_count.started,
                    "stop_at": floating_ip_count.stopped,
                    "amount": floating_ip_count.amount,
                    "hour": (floating_ip_count.stopped - floating_ip_count.started).total_seconds() / 3600,
                }
            )

        context = {
            "invoice": invoice,
            "virtances": virtance_list,
            "snapshots": snapshot_list,
            "floating_ips": floating_ip_list,
        }
        template = get_template("pdf/invoice.html")
        html_content = template.render(context)

        response = HttpResponse(content_type="application/pdf")
        response[
            "Content-Disposition"
        ] = f"attachment; filename='inovoice-{invoice.create.year}-{invoice.create.month}.pdf'"
        HTML(string=html_content).write_pdf(response)
        return response
