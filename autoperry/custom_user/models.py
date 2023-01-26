from django_use_email_as_username.models import BaseUser, BaseUserManager
from django.db import models
from django.utils.translation import gettext_lazy as _

class User(BaseUser):
    objects = BaseUserManager()

    # Copied from django.contrib.auth.models.AbstractUser so we can override
    # blank to False
    first_name = models.CharField(_("first name"), max_length=150, blank=False)
    last_name = models.CharField(_("last name"), max_length=150, blank=False)

    cancelled = models.DateTimeField(null=True, blank=True, help_text="Timestamp of account cancellation")
    send_notifications = models.BooleanField(null=False, default=True, help_text="Send email reminders and other messages", verbose_name="send email notifications")
    email_validated = models.DateTimeField(null=True, blank=True, help_text="Timestamp of email address validation")
    reminded_upto = models.DateTimeField(null=True, blank=True, help_text="End date of most recent reminder run")
    suspended = models.DateTimeField(null=True, blank=True, help_text="Timestamp of suspension")

    def __str__(self):
        return self.get_full_name()

    @property
    def is_enabled(self):
        return (self.is_authenticated and
                self.email_validated and
                not self.suspended and
                not self.cancelled)



