from django.urls import re_path

from billing.views import BalanceAPI, BillingHistoryListAPI, InvoiceListAPI, InvoiceDataAPI

urlpatterns = [
    re_path(r"balance/?$", BalanceAPI.as_view(), name="balance_api"),
    re_path(r"history/?$", BillingHistoryListAPI.as_view(), name="billing_history_list_api"),
    re_path(r"invoices/?$", InvoiceListAPI.as_view(), name="invoice_list_api"),
    re_path(r"invoices/(?P<uuid>[0-9a-f-]+)/?$", InvoiceDataAPI.as_view(), name="invoice_data_api"),
]
