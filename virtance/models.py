from uuid import uuid4
from django.db import models
from django.conf import settings
from django.utils import timezone


class Virtance(models.Model):
    CREATE = "create"
    DELETE = "delete"
    REBOOT = "reboot"
    RESIZE = "resize"
    RENAME = "rename"
    REBUILD = "rebuild"
    RESTORE = "restore"
    SNAPSHOT = "snapshot"
    SHUTDOWN = "shutdown"
    POWER_ON = "power_on"
    POWER_OFF = "power_off"
    PASSWORD_RESET = "password_reset"
    ENABLE_BACKUPS = "enable_backups"
    DISABLE_BACKUPS = "disable_backups"
    ENABLE_RECOVERY_MODE = "enable_recovery_mode"
    DISABLE_RECOVERY_MODE = "disable_recovery_mode"
    EVENT_CHOICES = [
        (CREATE, "Create"),
        (DELETE, "Delete"),
        (REBOOT, "Reboot"),
        (RESIZE, "Resize"),
        (RENAME, "Rename"),
        (REBUILD, "Rebuild"),
        (RESTORE, "Restore"),
        (SNAPSHOT, "Snapshot"),
        (SHUTDOWN, "Shutdown"),
        (POWER_ON, "Power On"),
        (POWER_OFF, "Power Off"),
        (PASSWORD_RESET, "Password Reset"),
        (ENABLE_BACKUPS, "Enable Backups"),
        (DISABLE_BACKUPS, "Disable Backups"),
        (ENABLE_RECOVERY_MODE, "Enable Recovery Mode"),
        (DISABLE_RECOVERY_MODE, "Disable Recovery Mode")
    ]
    ACTIVE = "active"
    PENDING = "pending"
    INACTIVE = "inactive"
    STATUS_CHOICES = (
        (ACTIVE, "Active"),
        (PENDING, "Pending"),
        (INACTIVE, "Inactive"),
    )
    user = models.ForeignKey(settings.AUTH_USER_MODEL, models.PROTECT)
    size = models.ForeignKey("size.Size", models.PROTECT)
    region = models.ForeignKey("region.Region", models.PROTECT)
    compute = models.ForeignKey("compute.Compute", models.PROTECT, null=True, blank=True)
    template = models.ForeignKey("image.Image", models.PROTECT)
    event = models.CharField(max_length=40, choices=EVENT_CHOICES, blank=True, null=True)
    uuid = models.UUIDField(unique=True, editable=False, default=uuid4)
    name = models.CharField(max_length=100)
    disk = models.BigIntegerField()
    status = models.CharField(max_length=100, choices=STATUS_CHOICES, default=PENDING)
    user_data = models.TextField(blank=True, null=True)
    is_locked = models.BooleanField(default=False)
    is_deleted = models.BooleanField(default=False)
    is_recovery_mode = models.BooleanField(default=False)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    deleted = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-id"]
        verbose_name = "Virtance"
        verbose_name_plural = "Virtances"

    def active(self):
        self.status = self.ACTIVE
        self.save()

    def inactive(self):
        self.status = self.INACTIVE
        self.save()

    def pending(self):
        self.status = self.PENDING
        self.save()

    def reset_event(self):
        self.event = None
        self.save()

    def enable_recovery_mode(self):
        self.is_recovery_mode = True
        self.save()

    def disable_recovery_mode(self):
        self.is_recovery_mode = False
        self.save()

    def save(self, *args, **kwargs):
        self.updated = timezone.now()
        super(Virtance, self).save(*args, **kwargs)

    def delete(self):
        self.is_deleted = True
        self.deleted = timezone.now()
        self.reset_event()
        self.save()

    def __unicode__(self):
        return self.name


class VirtanceCounter(models.Model):
    virtance = models.ForeignKey(Virtance, models.PROTECT)
    size = models.ForeignKey("size.Size", models.PROTECT)
    amount = models.DecimalField(max_digits=12, decimal_places=6, default=0.0)
    started = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    stopped = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ["-id"]
        verbose_name = "Virtance Counter"
        verbose_name_plural = "Virtance Counters"

    def stop(self):
        self.stopped = timezone.now()
        self.save()

    def __unicode__(self):
        return self.started


class VirtanceError(models.Model):
    virtance = models.ForeignKey(Virtance, models.PROTECT)
    event = models.CharField(max_length=40, blank=True, null=True)
    message = models.TextField()
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-id"]
        verbose_name = "Virtance Error"
        verbose_name_plural = "Virtance Errors"

    def __unicode__(self):
        return self.event
