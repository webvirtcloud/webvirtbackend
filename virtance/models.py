from uuid import uuid4

from django.conf import settings
from django.db import models
from django.utils import timezone


class Virtance(models.Model):
    ACTIVE = "active"
    PENDING = "pending"
    INACTIVE = "inactive"
    STATUS_CHOICES = (
        (ACTIVE, "Active"),
        (PENDING, "Pending"),
        (INACTIVE, "Inactive"),
    )

    CREATE = "create"
    DELETE = "delete"
    REBOOT = "reboot"
    RESIZE = "resize"
    RENAME = "rename"
    BACKUP = "backup"
    REBUILD = "rebuild"
    RESTORE = "restore"
    SNAPSHOT = "snapshot"
    SHUTDOWN = "shutdown"
    POWER_ON = "power_on"
    POWER_OFF = "power_off"
    POWER_CYCLE = "power_cycle"
    PASSWORD_RESET = "password_reset"
    ENABLE_BACKUPS = "enable_backups"
    DISABLE_BACKUPS = "disable_backups"
    FIREWALL_ATTACH = "firewall_attach"
    FIREWALL_DETACH = "firewall_detach"
    ASSIGN_FLOATING_IP = "assign_floating_ip"
    UNASSIGN_FLOATING_IP = "unassign_floating_ip"
    ENABLE_RECOVERY_MODE = "enable_recovery_mode"
    DISABLE_RECOVERY_MODE = "disable_recovery_mode"
    EVENT_CHOICES = (
        (CREATE, "Create"),
        (DELETE, "Delete"),
        (REBOOT, "Reboot"),
        (RESIZE, "Resize"),
        (RENAME, "Rename"),
        (BACKUP, "Backup"),
        (REBUILD, "Rebuild"),
        (RESTORE, "Restore"),
        (SNAPSHOT, "Snapshot"),
        (SHUTDOWN, "Shutdown"),
        (POWER_ON, "Power On"),
        (POWER_OFF, "Power Off"),
        (POWER_CYCLE, "Power Cycle"),
        (PASSWORD_RESET, "Password Reset"),
        (ENABLE_BACKUPS, "Enable Backups"),
        (DISABLE_BACKUPS, "Disable Backups"),
        (FIREWALL_ATTACH, "Attach Firewall"),
        (FIREWALL_DETACH, "Detach Firewall"),
        (ASSIGN_FLOATING_IP, "Assign Floating IP"),
        (UNASSIGN_FLOATING_IP, "Unassign Floating IP"),
        (ENABLE_RECOVERY_MODE, "Enable Recovery Mode"),
        (DISABLE_RECOVERY_MODE, "Disable Recovery Mode"),
    )

    K8AAS = "k8aas"
    DBAAS = "dbaas"
    LBAAS = "lbaas"
    VIRTANCE = "virtance"
    TYPE_CHOICES = (
        (VIRTANCE, "Virtance"),
        (K8AAS, "Kubernetes"),
        (DBAAS, "Database"),
        (LBAAS, "Load Balancer"),
    )

    user = models.ForeignKey(settings.AUTH_USER_MODEL, models.PROTECT)
    size = models.ForeignKey("size.Size", models.PROTECT)
    region = models.ForeignKey("region.Region", models.PROTECT)
    compute = models.ForeignKey("compute.Compute", models.PROTECT, null=True, blank=True)
    template = models.ForeignKey("image.Image", models.PROTECT)
    type = models.CharField(max_length=40, choices=TYPE_CHOICES, default=VIRTANCE)
    event = models.CharField(max_length=40, choices=EVENT_CHOICES, default=CREATE, blank=True, null=True)
    uuid = models.UUIDField(unique=True, editable=False, default=uuid4)
    name = models.CharField(max_length=100)
    disk = models.BigIntegerField()
    status = models.CharField(max_length=100, choices=STATUS_CHOICES, default=PENDING)
    user_data = models.TextField(blank=True, null=True)
    is_locked = models.BooleanField(default=False)
    is_deleted = models.BooleanField(default=False)
    is_recovery_mode = models.BooleanField(default=False)
    is_backup_enabled = models.BooleanField(default=False)
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

    def enable_backups(self):
        self.is_backup_enabled = True
        self.save()

    def disable_backups(self):
        self.is_backup_enabled = False
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
    backup_amount = models.DecimalField(max_digits=12, decimal_places=6, default=0.0)
    license_amount = models.DecimalField(max_digits=12, decimal_places=6, default=0.0)
    started = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    stopped = models.DateTimeField(blank=True, null=True)

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


class VirtanceHistory(models.Model):
    virtance = models.ForeignKey(Virtance, models.PROTECT)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, models.PROTECT)
    event = models.CharField(max_length=40)
    message = models.TextField(blank=True, null=True)
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-id"]
        verbose_name = "Virtance History"
        verbose_name_plural = "Virtance Histories"

    def __unicode__(self):
        return self.event
