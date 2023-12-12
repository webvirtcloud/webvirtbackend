from uuid import uuid4
from django.db import models


class Invoice(models.Model):
    uuid = models.UUIDField(unique=True, editable=False, default=uuid4)
    user = models.ForeignKey("account.User", on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    create = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Invoice"
        verbose_name_plural = "Invoices"
        ordering = ["-id"]

    def __unicode__(self):
        return self.amount


class Balance(models.Model):
    user = models.ForeignKey("account.User", on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    create = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Balance"
        verbose_name_plural = "Balances"
        ordering = ["-id"]

    def __unicode__(self):
        return self.balance
