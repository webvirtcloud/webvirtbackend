from uuid import uuid4
from django.db import models
from django.conf import settings
from django.utils import timezone


class LBaaS(models.Model):
    TCP = "tcp"
    HTTP = "http"
    HTTPS = "https"
    CHECK_PROTOCOL_CHOICES = (
        (TCP, "TCP"),
        (HTTP, "HTTP"),
        (HTTPS, "HTTPS"),
    )

    CREATE = "create"
    DELETE = "delete"
    ADD_VIRTANCE = "add_virtance"
    REMOVE_VIRTANCE = "remove_virtance"
    ADD_FORWARD_RULE = "add_forward_rule"
    REMOVE_FORWARD_RULE = "remove_forward_rule"
    EVENT_CHOICES = (
        (CREATE, "Create"),
        (DELETE, "Delete"),
        (ADD_VIRTANCE, "Add Virtance to a Load Balancer"),
        (REMOVE_VIRTANCE, "Remove Virtance from a Load Balancer"),
        (ADD_FORWARD_RULE, "Add Forwarding Rules to a Load Balancer"),
        (REMOVE_FORWARD_RULE, "Remove Forwarding Rules to a Load Balancer"),
    )

    uuid = models.UUIDField(unique=True, editable=False, default=uuid4)
    name = models.CharField(max_length=100)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, models.PROTECT)
    virtance = models.ForeignKey("virtances.Virtance", models.PROTECT)
    event = models.CharField(max_length=40, choices=EVENT_CHOICES, default=CREATE, blank=True, null=True)
    check_protocol = models.CharField(max_length=10, choices=CHECK_PROTOCOL_CHOICES, default=TCP)
    check_port = models.IntegerField(default=80)
    check_path = models.CharField(max_length=100, default="/")
    check_interval_seconds = models.IntegerField(default=10)
    check_timeout_seconds = models.IntegerField(default=2)
    check_unhealthy_threshold = models.IntegerField(default=5)
    check_healthy_threshold = models.IntegerField(default=3)
    sticky_sessions = models.BooleanField(default=False)
    sticky_sessions_cookie_name = models.CharField(max_length=100, default="sessionid")
    sticky_sessions_cookie_ttl = models.IntegerField(default=3600)
    redirect_http_to_https = models.BooleanField(default=False)
    is_deleted = models.BooleanField("Deleted", default=False)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    deleted = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "Load Balancer"
        verbose_name_plural = "Load Balancers"
        ordering = ["-id"]

    def __unicode__(self):
        return self.name

    def save(self, *args, **kwargs):
        self.updated = timezone.now()
        super(LBaaS, self).save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        self.is_active = False
        self.deleted = timezone.now()
        self.is_deleted = True
        self.save()


class LBaaSForwadRule(models.Model):
    UDP = "udp"
    TCP = "tcp"
    HTTP = "http"
    HTTPS = "https"
    HTTP2 = "http2"
    HTTP3 = "http3"
    PROTOCOL_CHOICES = (
        (UDP, "UDP"),
        (TCP, "TCP"),
        (HTTP, "HTTP"),
        (HTTPS, "HTTPS"),
    )

    lbaas = models.ForeignKey(LBaaS, models.PROTECT)
    entry_port = models.IntegerField()
    entry_protocol = models.CharField(max_length=10, choices=PROTOCOL_CHOICES, default=HTTP)
    target_port = models.IntegerField()
    target_protocol = models.CharField(max_length=10, choices=PROTOCOL_CHOICES, default=HTTP)
    is_deleted = models.BooleanField("Deleted", default=False)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    deleted = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "Load Balancer Forward Rule"
        verbose_name_plural = "Load Balancer Forward Rules"
        ordering = ["-id"]

    def __unicode__(self):
        return self.name

    def save(self, *args, **kwargs):
        self.updated = timezone.now()
        super(LBaaSForwadRule, self).save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        self.is_active = False
        self.deleted = timezone.now()
        self.is_deleted = True
        self.save()


class LBaaSVirtance(models.Model):
    lbaas = models.ForeignKey(LBaaS, models.PROTECT)
    virtance = models.ForeignKey("virtances.Virtance", models.PROTECT)
    is_deleted = models.BooleanField("Deleted", default=False)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    deleted = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "Load Balancer Virtance"
        verbose_name_plural = "Load Balancer Virtances"
        ordering = ["-id"]

    def __unicode__(self):
        return self.name

    def save(self, *args, **kwargs):
        self.updated = timezone.now()
        super(LBaaSVirtance, self).save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        self.is_active = False
        self.deleted = timezone.now()
        self.is_deleted = True
        self.save()
