from uuid import uuid4

from django.conf import settings
from django.db import models
from django.utils import timezone


class DBaaS(models.Model):
    CREATE = "create"
    DELETE = "delete"
    REBOOT = "reboot"
    RESIZE = "resize"
    RENAME = "rename"
    RESTORE = "restore"
    SNAPSHOT = "snapshot"
    SHUTDOWN = "shutdown"
    POWER_ON = "power_on"
    POWER_OFF = "power_off"
    POWER_CYCLE = "power_cycle"
    PASSWORD_RESET = "password_reset"
    ENABLE_BACKUPS = "enable_backups"
    DISABLE_BACKUPS = "disable_backups"
    EVENT_CHOICES = (
        (CREATE, "Database is creating..."),
        (DELETE, "Database is deleting..."),
        (REBOOT, "Database is rebooting..."),
        (RESIZE, "Database is resizing..."),
        (RENAME, "Database is renaming..."),
        (RESTORE, "Database is restoring..."),
        (SNAPSHOT, "Database is taking a snapshot..."),
        (SHUTDOWN, "Database is shutting down..."),
        (POWER_ON, "Database is powering on..."),
        (POWER_OFF, "Database is powering off..."),
        (POWER_CYCLE, "Database is power cycling..."),
        (PASSWORD_RESET, "Reseting password..."),
        (ENABLE_BACKUPS, "Backups are being enabled..."),
        (DISABLE_BACKUPS, "Backups are being disabled..."),
    )

    uuid = models.UUIDField(unique=True, editable=False, default=uuid4)
    name = models.CharField(max_length=100)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, models.PROTECT)
    dbms = models.ForeignKey("size.DBMS", models.PROTECT)
    virtance = models.ForeignKey("virtance.Virtance", models.PROTECT, blank=True, null=True)
    event = models.CharField(max_length=40, choices=EVENT_CHOICES, default=CREATE, blank=True, null=True)
    private_key = models.TextField()
    admin_secret = models.TextField()
    master_secret = models.TextField()
    is_deleted = models.BooleanField("Deleted", default=False)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    deleted = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "Database"
        verbose_name_plural = "Databases"
        ordering = ["-id"]

    def __unicode__(self):
        return self.name

    def reset_event(self):
        self.event = None
        self.save()

    def save(self, *args, **kwargs):
        self.updated = timezone.now()
        super(DBaaS, self).save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        self.is_active = False
        self.deleted = timezone.now()
        self.is_deleted = True
        self.save()
