# webapp/forms.py

from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import get_user_model
from django import forms
from django.utils import timezone
from django.core.exceptions import ValidationError

from datetime import timedelta

class CustomUserCreationForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        fields = list(UserCreationForm.Meta.fields) + ["email", "first_name", "last_name"]
        fields.remove("username")
        model = get_user_model()


class EventForm(forms.Form):
    start = forms.DateTimeField(help_text='When the event starts, for example 2022-12-09 19:30', initial=timezone.now().strftime("%Y-%m-%d") + " 19:30")
    duration = forms.DurationField(help_text='The length of the event, for example 01:30:00 for an hour and a half', initial="01:30:00")
    location = forms.CharField(max_length=60, help_text='Where the event takes place')
    helpers_required = forms.IntegerField(min_value=1, help_text='Number of helpers wanted')

    def clean_start(self):
        start = self.cleaned_data['start']
        if start < timezone.now():
            raise ValidationError("This date/time is in the past. Events must start in the future!")
        return start

    def clean_duration(self):
        duration = self.cleaned_data['duration']
        if duration < timedelta(minutes=15):
            raise ValidationError("This is less that 15 minutes. Events must be more that 15 minutes long!")
        return duration
