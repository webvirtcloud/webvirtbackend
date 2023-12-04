from django.urls import re_path

from billing.views import BalanceAPI, InvoiceHistoryAPI

urlpatterns = [
    re_path(r"balance/?$", BalanceAPI.as_view(), name="balance_api"),
    re_path(r"history/?$", InvoiceHistoryAPI.as_view(), name="invoice_history_api"),
]
