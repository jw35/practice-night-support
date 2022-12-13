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
    start = forms.SplitDateTimeField(help_text='Event start date ("YYY-MM-DD") & time (HH:MM)',
        initial=timezone.now().replace(hour=19, minute=30, second=0),
        widget=forms.SplitDateTimeWidget(time_format='%H:%M'))
    hours = forms.IntegerField(min_value=0, max_value=24, help_text="Duration - hours")
    minutes = forms.IntegerField(min_value=0, max_value=59, help_text="Duration - minutes")
    location = forms.CharField(max_length=60, help_text='Where the event takes place')
    helpers_required = forms.IntegerField(min_value=1, help_text='Number of helpers wanted')

    def clean_start(self):
        start = self.cleaned_data['start']
        if start < timezone.now():
            raise ValidationError("This date/time is in the past. Events must start in the future!")
        return start

