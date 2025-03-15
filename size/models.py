from django.db import models
from django.utils import timezone


class Size(models.Model):
    LBAAS = "lbaas"
    VIRTANCE = "virtance"
    TYPE_CHOICES = (
        (LBAAS, "Load Balancer"),
        (VIRTANCE, "Virtance"),
    )

    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=100, unique=True)
    type = models.CharField(max_length=50, choices=TYPE_CHOICES, default=VIRTANCE)
    description = models.TextField(blank=True, null=True)
    vcpu = models.IntegerField()
    disk = models.BigIntegerField()
    memory = models.BigIntegerField()
    transfer = models.BigIntegerField()
    regions = models.ManyToManyField("region.Region", related_name="regions")
    is_active = models.BooleanField("Active", default=False)
    is_deleted = models.BooleanField("Deleted", default=False)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now_add=True)
    deleted = models.DateTimeField(blank=True, null=True)
    price = models.DecimalField(max_digits=12, decimal_places=6, default=0.0)

    class Meta:
        verbose_name = "Size"
        verbose_name_plural = "Sizes"
        ordering = ["-type", "memory", "vcpu", "disk", "transfer"]

    def save(self, *args, **kwargs):
        self.updated_at = timezone.now()
        super(Size, self).save(*args, **kwargs)

    def delete(self):
        self.is_active = False
        self.is_deleted = True
        self.deleted = timezone.now()
        self.save()

    def __unicode__(self):
        return self.name


class DBMS(models.Model):
    PGSQL = "pgsql"
    ENGINE_CHOICES = ((PGSQL, "PostgreSQL"),)

    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=100, unique=True)
    description = models.CharField(max_length=255, blank=True)
    required_size = models.ForeignKey(Size, models.SET_NULL, blank=True, null=True)
    engine = models.CharField(max_length=10, choices=ENGINE_CHOICES)
    version = models.CharField(max_length=20)
    is_active = models.BooleanField("Active", default=False)
    is_deleted = models.BooleanField("Deleted", default=False)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now_add=True)
    deleted = models.DateTimeField(blank=True, null=True)

    class Meta:
        verbose_name = "Database Management System"
        verbose_name_plural = "Database Management Systems"
        ordering = ["-id"]

    def save(self, *args, **kwargs):
        self.updated_at = timezone.now()
        super(Size, self).save(*args, **kwargs)

    def delete(self):
        self.is_active = False
        self.is_deleted = True
        self.deleted = timezone.now()
        self.save()

    def __unicode__(self):
        return self.name
