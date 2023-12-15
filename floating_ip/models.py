from django.db import models
from django.utils import timezone


class FloatIP(models.Model):
    CREATE = "create"
    DELETE = "delete"
    ASSIGN = "assign"
    UNASSIGN = "unassign"
    EVENT_CHOICES = [
        (CREATE, "Creating"),
        (DELETE, "Deleting"),
        (ASSIGN, "Assigning"),
        (UNASSIGN, "Unassigning"),
    ]
    user = models.ForeignKey("account.User", models.PROTECT)
    event = models.CharField(max_length=40, choices=EVENT_CHOICES, blank=True, null=True)
    cidr = models.CharField(max_length=32, blank=True, null=True)
    ipaddress = models.ForeignKey("network.IPAddress", models.PROTECT, blank=True, null=True)
    is_deleted = models.BooleanField(default=False)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField()
    deleted = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-id"]
        verbose_name = "FloatingIP"
        verbose_name_plural = "FloatingIPs"

    def reset_event(self):
        self.event = None
        self.save()

    def save(self, *args, **kwargs):
        self.updated = timezone.now()
        super(FloatIP, self).save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        self.event = None
        self.ipaddress = None
        self.is_deleted = True
        self.deleted = timezone.now()
        self.save()

    def __unicode__(self):
        return self.ipaddress.address


class FloatIPCounter(models.Model):
    floatip = models.ForeignKey(FloatIP, models.PROTECT)
    ipaddress = models.GenericIPAddressField()
    amount = models.DecimalField(max_digits=12, decimal_places=6, default=0.0)
    started = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    stopped = models.DateTimeField(blank=True, null=True)

    class Meta:
        ordering = ["-id"]
        verbose_name = "FloatingIP Counter"
        verbose_name_plural = "FloatingIPs Counters"

    def stop(self):
        self.stopped = timezone.now()
        self.save()

    def __unicode__(self):
        return self.started


class FloatIPError(models.Model):
    floatip = models.ForeignKey(FloatIP, models.PROTECT)
    event = models.CharField(max_length=40, blank=True, null=True)
    message = models.TextField()
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-id"]
        verbose_name = "Floating IP Error"
        verbose_name_plural = "Floating IPs Errors"

    def __unicode__(self):
        return self.event
