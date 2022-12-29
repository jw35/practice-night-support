from django.db import models
from django.utils import timezone
from django.utils.dateformat import format
from django.urls import reverse

from custom_user.models import User


# Create your models here.

class Event(models.Model):
    start = models.DateTimeField(blank=False)
    duration = models.DurationField(blank=False)
    location = models.CharField(max_length=128, blank=False)
    helpers_required = models.IntegerField(blank=False)
    owner = models.ForeignKey(User, models.DO_NOTHING, related_name='events_owned')
    helpers = models.ManyToManyField(User, through="Volunteer", related_name='events_volunteered')
    created = models.DateTimeField(auto_now_add=True)
    cancelled = models.DateTimeField(null=True, blank=True)

    @property
    def end(self):
        return self.start + self.duration

    @property
    def past(self):
        return self.start < timezone.now()

    @property
    def helpers_needed(self):
        return self.helpers_required > len(self.helpers.all()) and not self.cancelled and not self.past

    @property
    def when(self):
        start = self.start
        end = start + self.duration
        if start.hour <12 and end.hour >= 12:
            # Either side of midday
            return (format(start, "D, j M Y, g:i a") +
                    ' to ' +
                    format(end, "g:i a"))
        else:
            return (format(start, "D, j M Y, g:i") +
                    ' to ' +
                    format(end, "g:i a"))

    def get_absolute_url(self):
        return reverse('event-details', args=[self.pk])

    def __str__(self):
    	return (self.location +
    		    ': ' +
    		    self.start.strftime('%A %d %B %Y') +
    		    ' (' +
    		    self.start.strftime('%H:%M') +
    		    '-' +
    		    (self.start + self.duration).strftime('%H:%M') +
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
