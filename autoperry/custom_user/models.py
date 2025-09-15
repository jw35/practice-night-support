from django_use_email_as_username.models import BaseUser, BaseUserManager
from django.contrib import admin
from django.db import models
from django.apps import apps
from django.template.defaultfilters import force_escape, urlize
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _


class User(BaseUser):
    objects = BaseUserManager()

    # Copied from django.contrib.auth.models.AbstractUser so we can override
    # blank to False
    first_name = models.CharField(_("first name"), max_length=150, blank=False)
    last_name = models.CharField(_("last name"), max_length=150, blank=False)

    cancelled = models.DateTimeField(null=True, blank=True, help_text="Timestamp of account cancellation")
    send_notifications = models.BooleanField(null=False, default=True, help_text="Send email alerts and reminders about your events", verbose_name="send event emails")
    email_validated = models.DateTimeField(null=True, blank=True, help_text="Timestamp of email address validation")
    reminded_upto = models.DateTimeField(null=True, blank=True, help_text="End date of most recent reminder run")
    suspended = models.DateTimeField(null=True, blank=True, help_text="Timestamp of suspension")
    approved = models.DateTimeField(null=True, blank=True, help_text="Timestamp of approval")
    tower = models.CharField(max_length=50, blank=False, help_text="Where you normally ring")
    send_other = models.BooleanField(null=False, default=True, verbose_name="send other emails")
    uuid = models.CharField(max_length=64, blank=True)
    phone_number = models.CharField(max_length=64, blank=True, help_text="Optional, useful in case of last-minute cancellations or changes of plan")
    volunteer_celebration = models.IntegerField(null=False, default=0, help_text="Highest volunteer count celebrated")
    email_blocked = models.DateTimeField(null=True, blank=True, help_text="Timestamp of email suspension")

    # Additional magic fields
    #
    # events_volountered (from webapp.models.event)
    # events_owned (from webapp.models.event)
    # volunteer_set (filter volunteer, from webapp.volunteer) to access the individual volunteering records

    def __str__(self):
        return f'{self.get_full_name()} [#{self.pk}]'

    @property
    def contact_info(self):

        """
        Email address as link, and phone number if there is one
        """
        result = urlize(self.email)
        if self.phone_number:
            result += f', {force_escape(self.phone_number)}'
        return mark_safe(result)


    @property
    def contact_info_text(self):

        """
        Email address as text, and phone number if there is one
        """
        result = self.email
        if self.phone_number:
            result += f', {self.phone_number}'
        return result


    @property
    @admin.display(boolean=True)
    def is_enabled(self):

        """
        Is the user allowed to interact with the core of AutoPerry?
        Needs to be an actual user (not Anonymous), to be approved and to
        have a validated email address, and not to be suspended or cancelled.
        """

        return (self.is_authenticated and
                self.approved and
                self.email_validated and
                not self.suspended and
                not self.cancelled)

    @property
    @admin.display(boolean=True)
    def is_email_validated(self):
        return self.email_validated != None

    @property
    @admin.display(boolean=True)
    def is_approved(self):
        return self.approved != None

    @property
    @admin.display(boolean=True)
    def is_suspended(self):
        return self.suspended != None

    @property
    @admin.display(boolean=True)
    def is_cancelled(self):
        return self.cancelled != None

    @property
    @admin.display(boolean=True)
    def is_email_blocked(self):
        return self.email_blocked != None

    @property
    def n_events_helped(self):
        """
        Return the number of events at which the user helped
        """
        return (apps.get_model('webapp', 'Event').objects.
            filter(
                volunteer__person=self,
                volunteer__withdrawn=None,
                volunteer__declined=None
            ).count()
       )

    @property
    def n_events_owned(self):
        """
        Return the number of events at which the user helped
        """
        return (self.events_owned.all().count())




    class Meta:

        permissions = [
            ('administrator', 'Is system administrator')
        ]



