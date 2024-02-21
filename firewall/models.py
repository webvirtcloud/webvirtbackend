import re
from uuid import uuid4
from django.db import models
from django.utils import timezone
from django.core.exceptions import ValidationError


def validate_ports(value):
    pattern = r"^(\d{1,5}|\d{1,5}-\d{1,5})$"
    if not re.match(pattern, value):
        raise ValidationError("Invalid format. Use '80' or '80-110'.")


class Firewall(models.Model):
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    ATTACH = "attach"
    DETACH = "detach"
    EVENT_CHOICES = [
        (CREATE, "Creating"),
        (UPDATE, "Updating"),
        (DELETE, "Deleting"),
        (ATTACH, "Attaching"),
        (DETACH, "Detaching"),
    ]

    uuid = models.UUIDField(unique=True, editable=False, default=uuid4)
    user = models.ForeignKey("account.User", models.PROTECT)
    name = models.CharField(max_length=50, blank=False)
    event = models.CharField(max_length=40, choices=EVENT_CHOICES, blank=True, null=True)
    is_deleted = models.BooleanField(default=False)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField()
    deleted = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "Firewall"
        verbose_name_plural = "Firewalls"
        ordering = ["-id"]

    def reset_event(self):
        self.event = None
        self.save()

    def save(self, *args, **kwargs):
        self.updated = timezone.now()
        super(Firewall, self).save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        self.is_deleted = True
        self.deleted = timezone.now()
        self.save()

    def __unicode__(self):
        return self.name


class Rule(models.Model):
    TCP = "tcp"
    UDP = "udp"
    ICMP = "icmp"
    PROTOCOL_CHOICES = [
        (TCP, "TCP"),
        (UDP, "UDP"),
        (ICMP, "ICMP"),
    ]

    DROP = "DROP"
    ACCEPT = "ACCEPT"
    ACTION_CHOICES = [
        (DROP, "DROP"),
        (ACCEPT, "ACCEPT"),
    ]

    INBOUND = "inbound"
    OUTBOUND = "outbound"
    DIRECTION_CHOICES = [
        (INBOUND, "Inbound"),
        (OUTBOUND, "Outbound"),
    ]

    firewall = models.ForeignKey(Firewall, models.PROTECT)
    direction = models.CharField(max_length=10, choices=DIRECTION_CHOICES)
    protocol = models.CharField(max_length=10, blank=True, null=True, choices=PROTOCOL_CHOICES)
    action = models.CharField(max_length=50, choices=ACTION_CHOICES, default=DROP)
    ports = models.CharField(max_length=12, validators=[validate_ports], default=0)
    created = models.DateTimeField(auto_now_add=True)
    is_system = models.BooleanField(default=False)

    class Meta:
        verbose_name = "Firewall Rule"
        verbose_name_plural = "Firewall Rules"
        ordering = ["-id"]

    def __unicode__(self):
        return self.direction


class Cidr(models.Model):
    rule = models.ForeignKey(Rule, models.PROTECT)
    address = models.GenericIPAddressField(default="0.0.0.0")
    prefix = models.IntegerField(default=0)
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "CIDR"
        verbose_name_plural = "CIDRs"
        ordering = ["-id"]

    def get_cidr(self):
        return f"{self.address}/{self.prefix}"

    def __unicode__(self):
        return f"{self.address}/{self.prefix}"


class FirewallVirtance(models.Model):
    firewall = models.ForeignKey(Firewall, models.PROTECT)
    virtance = models.ForeignKey("virtance.Virtance", models.PROTECT)
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Firewall Virtance"
        verbose_name_plural = "Firewall Virtances"
        ordering = ["-id"]

    def __unicode__(self):
        return self.virtance.id


class FirewallError(models.Model):
    firewall = models.ForeignKey(Firewall, models.PROTECT)
    event = models.CharField(max_length=40, blank=True, null=True)
    message = models.TextField()
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-id"]
        verbose_name = "Firewall Error"
        verbose_name_plural = "Firewalls Errors"

    def __unicode__(self):
        return self.event
