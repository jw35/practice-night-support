from django_use_email_as_username.models import BaseUser, BaseUserManager
from django.db import models

class User(BaseUser):
    objects = BaseUserManager()

    cancelled = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.get_full_name()

