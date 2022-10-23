from django.db import models
from django.utils import timezone
from django.utils.crypto import get_random_string
from django.contrib.auth.models import BaseUserManager, AbstractBaseUser


class UserManager(BaseUserManager):
    def create_user(self, email, password=None):
        if not email:
            raise ValueError('Input email')

        user = self.model(
            email=self.normalize_email(email),
        )
        user.hash = get_random_string(length=40)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password):
        if not email:
            raise ValueError('Input email')

        user = self.create_user(
            email,
            password=password,
        )
        user.hash = get_random_string(length=40)
        user.is_admin = True
        user.save(using=self._db)
        return user


class User(AbstractBaseUser):

    uuid = models.UUIDField(
        unique=True, 
        editable=False, 
        default=uuid4
    )

    email = models.EmailField(
        max_length=255,
        unique=True,
    )

    hash = models.CharField(
        max_length=40,
    )

    is_admin = models.BooleanField(
        default=False,
    )

    is_active = models.BooleanField(
        'Active',
        default=True,
    )

    first_name = models.CharField(
        max_length=50,
        blank=True,
    )

    last_name = models.CharField(
        max_length=50,
        blank=True,
    )

    date_joined = models.DateTimeField(
        auto_now_add=True,
    )

    is_verified = models.BooleanField(
        default=False,
    )

    objects = UserManager()

    USERNAME_FIELD = 'email'

    def get_full_name(self):
        return self.first_name + ' ' + self.last_name

    def get_short_name(self):
        return self.first_name + ' ' + self.last_name[0]

    def __str__(self):
        return self.email

    def has_perm(self, perm, obj=None):
        return True

    def has_module_perms(self, app_label):
        return True

    @property
    def is_superuser(self):
        return self.is_admin

    @property
    def is_staff(self):
        return self.is_admin

    def update_hash(self):
        self.hash = get_random_string(length=40)
        self.save()

    def activate(self):
        self.is_active = True
        self.save()

    class Meta:
        verbose_name = 'User'
        verbose_name_plural = 'Users'
