from django.db import models
from django.utils import timezone


class SizeQuerySet(models.QuerySet):
    def filter(self, *args, **kwargs):
        if "type" not in kwargs:
            kwargs["type"] = Size.VIRTANCE
        return super().filter(*args, **kwargs)


class SizeManager(models.Manager):
    def get_queryset(self):
        return SizeQuerySet(self.model, using=self._db)

    def filter(self, *args, **kwargs):
        return self.get_queryset().filter(*args, **kwargs)


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

    objects = SizeManager()

    class Meta:
        verbose_name = "Size"
        verbose_name_plural = "Sizes"
        ordering = ["memory", "vcpu", "disk", "transfer"]

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
