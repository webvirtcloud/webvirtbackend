from uuid import uuid4
from django.db import models
from django.conf import settings
from django.utils import timezone


class Image(models.Model):
    CUSTOM = "custom"
    BACKUP = "backup"
    SNAPSHOT = "snapshot"
    APPLICATION = "application"
    DISTRIBUTION = "distribution"
    TYPE_CHOICES = [
        (CUSTOM, "Custom"),
        (BACKUP, "Backup"),
        (SNAPSHOT, "Snapshot"),
        (APPLICATION, "Application"),
        (DISTRIBUTION, "Distribution"),
    ]
    UNKNOWN = "unknown"
    DEBIAN = "debian"
    UBUNTU = "ubuntu"
    FEDORA = "fedora"
    CENTOS = "centos"
    ALMALINUX = "almalinux"
    ROCKYLINUX = "rockylinux"
    DISTRO_CHOICES = [
        (UNKNOWN, "Unknown"),
        (DEBIAN, "Debian"),
        (UBUNTU, "Ubuntu"),
        (FEDORA, "Fedora"),
        (CENTOS, "CentOS"),
        (ALMALINUX, "AlmaLinux"),
        (ROCKYLINUX, "Rocky Linux"),
    ]
    CREATE = "create"
    DELETE = "delete"
    RESTORE = "restore"
    CONVERT = "convert"
    TRANSFER = "transfer"
    EVENT_CHOICES = [
        (CREATE, "Creating"),
        (DELETE, "Deleting"),
        (RESTORE, "Restoring"),
        (CONVERT, "Converting"),
        (TRANSFER, "Transfering"),
    ]
    user = models.ForeignKey(settings.AUTH_USER_MODEL, models.PROTECT, blank=True, null=True)
    source = models.ForeignKey("virtance.Virtance", models.PROTECT, blank=True, null=True)
    regions = models.ManyToManyField("region.Region", blank=True)
    uuid = models.UUIDField(unique=True, editable=False, default=uuid4)
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=100, unique=True, blank=True, null=True)
    type = models.CharField(max_length=50, choices=TYPE_CHOICES, default=SNAPSHOT)
    event = models.CharField(max_length=40, choices=EVENT_CHOICES, blank=True, null=True)
    md5sum = models.CharField(max_length=50)
    distribution = models.CharField(max_length=50, choices=DISTRO_CHOICES, default=UNKNOWN)
    description = models.TextField(blank=True, null=True)
    file_name = models.CharField(max_length=100)
    file_size = models.BigIntegerField(blank=True, null=True)
    disk_size = models.BigIntegerField(blank=True, null=True)
    is_active = models.BooleanField("Active", default=False)
    is_deleted = models.BooleanField("Deleted", default=False)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now_add=True)
    deleted = models.DateTimeField(blank=True, null=True)

    class Meta:
        verbose_name = "Image"
        verbose_name_plural = "Images"
        ordering = ["-id"]

    def reset_event(self):
        self.event = None
        self.save()

    def save(self, *args, **kwargs):
        self.updated = timezone.now()
        super(Image, self).save(*args, **kwargs)

    def delete(self):
        self.is_deleted = True
        self.deleted = timezone.now()
        self.reset_event()
        self.save()

    def __unicode__(self):
        return self.name


class ImageError(models.Model):
    image = models.ForeignKey(Image, models.PROTECT)
    event = models.CharField(max_length=40, blank=True, null=True)
    message = models.TextField()
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-id"]
        verbose_name = "Image Error"
        verbose_name_plural = "Image Errors"

    def __unicode__(self):
        return self.event
