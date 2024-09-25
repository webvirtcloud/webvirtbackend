from django.db import models
from django.utils import timezone


class Feature(models.Model):
    FEATURE_CHOICES = (
        ("ipv6", "IPv6"),
        ("resize", "Resize"),
        ("volume", "Volume"),
        ("backup", "Backup"),
        ("snapshot", "Snapshot"),
        ("one_click", "1Click"),
        ("floating_ip", "Float-IP"),
        ("load_balancer", "LBaaS"),
    )

    name = models.CharField(choices=FEATURE_CHOICES, unique=True, max_length=100)

    class Meta:
        verbose_name = "Feature"
        verbose_name_plural = "Features"
        ordering = ["id"]

    def __unicode__(self):
        return self.name


class Region(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)
    features = models.ManyToManyField("region.Feature", related_name="features")
    is_active = models.BooleanField("Active", default=False)
    is_deleted = models.BooleanField("Deleted", default=False)
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

    def delete(self):
        self.is_active = False
        self.is_deleted = True
        self.deleted = timezone.now()
        self.save()

    def __unicode__(self):
        return self.name
