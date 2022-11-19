import base64
import hashlib
from django.db import models
from django.utils import timezone


class SshKey(models.Model):
    name = models.CharField(max_length=100)
    public = models.CharField(max_length=1000)
    fingerprint = models.CharField(max_length=50)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "SSH Key"
        verbose_name_plural = "SSH Keys"
        ordering = ["-id"]

    def make_fingerprint(self):
        p_bytes = base64.b64decode(self.public.strip().split()[1])
        fp_plain = hashlib.md5(p_bytes).hexdigest()
        self.fingerprint = ":".join([fp_plain[i:i+2] for i in range(0, len(fp_plain), 2)])

    def __unicode__(self):
        return self.name

    def save(self, *args, **kwargs):
        self.updated = timezone.now()
        self.make_fingerprint()
        super(Image, self).save(*args, **kwargs)
