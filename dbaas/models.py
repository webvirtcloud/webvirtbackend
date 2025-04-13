from uuid import uuid4

from django.conf import settings
from django.db import models
from django.utils import timezone


class DBaaS(models.Model):
    CREATE = "create"
    RELOAD = "reload"
    DELETE = "delete"
    EVENT_CHOICES = (
        (CREATE, "Create"),
        (RELOAD, "Reload"),
        (DELETE, "Delete"),
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
