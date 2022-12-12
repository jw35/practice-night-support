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
    date = forms.DateField(help_text='Date of the event, for example 2022-12-09', initial=timezone.now().strftime("%Y-%m-%d"))
    time = forms.TimeField(help_text='When the event starts, for example 19:30', initial="19:30")
    hours = forms.IntegerField(min_value=0, max_value=24, help_text="Hours")
    minutes = forms.IntegerField(min_value=0, max_value=59, help_text="Minutes")
    location = forms.CharField(max_length=60, help_text='Where the event takes place')
    helpers_required = forms.IntegerField(min_value=1, help_text='Number of helpers wanted')
