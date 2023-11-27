from django.dispatch import receiver
from django.db.models.signals import post_save

from account.models import User
from .models import Balance


@receiver(post_save, sender=User)
def create_user_balance(sender, instance, **kwargs):
    if instance.pk is not None: 
        user = User.objects.get(pk=instance.pk)
        if user.is_email_verified is False and instance.is_email_verified is True:
            Balance.objects.create(user=instance, description="Initial balance")
