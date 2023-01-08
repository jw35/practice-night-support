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
    helpers_required = models.IntegerField(blank=False)
    owner = models.ForeignKey(User, models.DO_NOTHING, related_name='events_owned')
    helpers = models.ManyToManyField(User, through="Volunteer", related_name='events_volunteered')
    created = models.DateTimeField(auto_now_add=True)
    cancelled = models.DateTimeField(null=True, blank=True)
    contact_address = models.EmailField(blank=True, null=True, help_text="Contact email address for the event, defaults to owner's address")
    notes = models.CharField(max_length=128, blank=True, null=True, help_text="Purpose of the event, helper skills required, etc.")
    owner_reminded = models.DateTimeField(null=True, blank=True)

    @property
    def contact(self):
        if self.contact_address:
            return self.contact_address
        return self.owner.email

    @property
    def past(self):
        return self.start < timezone.now()

    @property
    def helpers_needed(self):
        return self.helpers_required > len(self.helpers.all()) and not self.cancelled and not self.past

    @property
    def when(self):
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


class Volunteer(models.Model):
    event = models.ForeignKey(Event, models.DO_NOTHING)
    person = models.ForeignKey(User, models.DO_NOTHING)
    created = models.DateTimeField(auto_now_add=True)
    cancelled = models.DateTimeField(null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['event', 'person'], name='only_volunteer_once')
        ]
