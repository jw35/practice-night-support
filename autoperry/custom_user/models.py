from django_use_email_as_username.models import BaseUser, BaseUserManager
from django.db import models

class User(BaseUser):
    objects = BaseUserManager()

    cancelled = models.DateTimeField(null=True, blank=True, help_text="Timestamp of account cancellation")
    send_notifications = models.BooleanField(null=False, default=True, help_text="Send email reminders and other messages", verbose_name="send email notifications")
    email_validated = models.DateTimeField(null=True, blank=True, help_text="Timestamp of email address validation")

    def __str__(self):
        return self.get_full_name()

