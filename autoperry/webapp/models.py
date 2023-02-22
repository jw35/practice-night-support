from django.contrib.auth import get_user_model
from django.db import models
from django.utils import timezone
from django.utils.dateformat import format
from django.urls import reverse

from custom_user.models import User


# Create your models here.

class Event(models.Model):
    start = models.DateTimeField(blank=False)
    end = models.DateTimeField(blank=False, null=True)
    location = models.CharField(max_length=128, blank=False)
    helpers_required = models.IntegerField(blank=False, verbose_name='helpers needed')
    owner = models.ForeignKey(User, models.DO_NOTHING, related_name='events_owned')
    helpers = models.ManyToManyField(User, through="Volunteer", related_name='events_volunteered')
    created = models.DateTimeField(auto_now_add=True)
    cancelled = models.DateTimeField(null=True, blank=True)
    contact_address = models.EmailField(blank=True, null=True, help_text="Contact email address for the event, defaults to owner's address")
    notes = models.CharField(max_length=200, blank=True, null=True, help_text="Purpose of the event, helper skills required, etc.")
    owner_reminded = models.DateTimeField(null=True, blank=True)
    alerts = models.BooleanField(default=False)
    # Also volunteer_set/volunteer to access the individual volunteering records


    def has_current_helper(self, user):
        """
        tests if user is a current (so not withdrawn, not declined)
        helpers for an event
        """
        return bool(self.volunteer_set.current().filter(person=user))


    @property
    def current_helpers(self):
        """
        Return a QuerySet representing all current (so not withdrawn,
        not declined) helpers for this event
        """
        return (get_user_model().objects.
            filter(
                volunteer__event=self,
                volunteer__withdrawn=None,
                volunteer__declined=None
            )
       )


    @property
    def contact(self):
        """
        Contact address for this event
        """
        if self.contact_address:
            return self.contact_address
        return self.owner.email


    @property
    def past(self):
        """
        Is this event in the past?
        """
        return self.start < timezone.now()


    @property
    def helpers_needed(self):
        """
        Does this event still need helpers?
        """
        return self.helpers_required > len(self.volunteer_set.current()) and not self.cancelled and not self.past

    @property
    def when(self):
        """
        Date of the event with start and end times
        """
        start = self.start
        end = self.end
        # Only include AM on start if event spans midday
        include_am = ''
        if start.hour <12 and end.hour >= 12:
            include_am = ' a'
        return (format(start, f"l, j F Y, g:i{include_am}") +
                ' to ' +
                format(end, "g:i a"))

    @property
    def short_when(self):
        """
        Short format d of the event with start and end times
        """
        start = self.start
        end = self.end
        # Only include year for December and January
        include_year = ''
        if start.month == 1 or start.month == 12:
            include_year = ' Y'
        # Only include AM on start if event spans midday
        include_am = ''
        if start.hour <12 and end.hour >= 12:
            include_am = ' a'
        return (format(start, f"D, j M{include_year}, g:i{include_am}") +
                '-' +
                format(end, f"g:i{include_am}"))

    def get_absolute_url(self):
        return reverse('event-details', args=[self.pk])

    def __str__(self):
    	return (self.location +
    		    ': ' +
    		    self.start.strftime('%A %d %B %Y') +
    		    ' (' +
    		    self.start.strftime('%H:%M') +
    		    '-' +
    		    self.end.strftime('%H:%M') +
    		    ')')

    class Meta:
        ordering = ["start"]


class VolunteerManager(models.Manager):

    """
    Add a custom method to only return volunteer objects that haven't
    been withdrawn or declined
    """

    def current(self):
        return self.filter(withdrawn=None, declined=None)


class Volunteer(models.Model):
    event = models.ForeignKey(Event, models.DO_NOTHING)
    person = models.ForeignKey(User, models.DO_NOTHING)
    created = models.DateTimeField(auto_now_add=True)
    withdrawn = models.DateTimeField(null=True, blank=True)
    declined = models.DateTimeField(null=True, blank=True)

    objects = VolunteerManager()

    @property
    def current(self):
        return self.withdrawn == None and self.declined == None

    def __str__(self):
        return f'{self.person} helping at {self.event}'

    class Meta:
        ordering = ["created"]

