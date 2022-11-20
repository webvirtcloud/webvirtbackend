from django.db import models
from django.utils import timezone

from size.models import Size


class Region(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)
    size = models.ManyToManyField(Size)
    is_active = models.BooleanField(default=False)
    is_deleted = models.BooleanField(default=False)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now_add=True)
    deleted = models.DateTimeField(blank=True, null=True)

    class Meta:
        verbose_name = "Region"
        verbose_name_plural = "Regions"
        ordering = ["-id"]

    def save(self, *args, **kwargs):
        self.updated = timezone.now()
        super(Region, self).save(*args, **kwargs)

    def __unicode__(self):
        return self.name
