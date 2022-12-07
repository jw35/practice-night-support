from django.db import models    

from custom_user.models import User


# Create your models here.

class Event(models.Model):
    start = models.DateTimeField(blank=False)
    duration = models.DurationField(blank=False)
    location = models.CharField(max_length=128, blank=False)
    helpers_required = models.IntegerField(blank=False)
    owner = models.ForeignKey(User, models.DO_NOTHING, related_name='owned_event_set')
    helpers = models.ManyToManyField(User, through="Volunteer", related_name='volunteered_event_set')
    created = models.DateTimeField(auto_now_add=True)
    cancelled = models.DateTimeField(null=True, blank=True)

    @property
    def end(self):
        return self.start + self.duration

    def __str__(self):
    	return (self.location +
    		    ' ' +
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
