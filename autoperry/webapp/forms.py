# webapp/forms.py

from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import get_user_model
from django import forms
from django.utils import timezone
from django.core.exceptions import ValidationError

from bootstrap_datepicker_plus.widgets import DatePickerInput, TimePickerInput

from datetime import date, time, datetime

class CustomUserCreationForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        fields = list(UserCreationForm.Meta.fields) + ["email", "first_name", "last_name", "send_notifications"]
        fields.remove("username")
        model = get_user_model()


class EventForm(forms.Form):
    date = forms.DateField(help_text='Event date', initial=date.today(), widget=DatePickerInput())
    start_time = forms.TimeField(help_text='Event start time', initial="19:30", widget=TimePickerInput())
    end_time = forms.TimeField(help_text='Event finish time', initial="21:00", widget=TimePickerInput(range_from="start_time"))
    location = forms.CharField(max_length=60, help_text='Where the event takes place')
    helpers_required = forms.IntegerField(min_value=1, help_text='Number of helpers wanted', initial=1)
    contact_address = forms.CharField(max_length=60, required=False, help_text="Email address for the event (yours if blank)")
    notes = forms.CharField(max_length=128, required=False, help_text="Purpose of the event, helper skills required, etc. (optional)")

    def clean(self):
        cleaned_data = super().clean()
        date = cleaned_data.get("date")
        start_time = cleaned_data.get("start_time")
        end_time = cleaned_data.get("end_time")

        if date and start_time and end_time:

            if start_time >= end_time:
                raise ValidationError("End time must be later than start time!")

            start = timezone.make_aware(datetime.combine(date, start_time))
            if start < timezone.now():
                raise ValidationError("Event start is in the past. Events must start in the future!")

class UserEditForm(forms.Form):
    email = forms.EmailField()
    first_name = forms.CharField(max_length=150)
    last_name = forms.CharField(max_length=150)
    send_notifications = forms.BooleanField(required=False,label="Send email notifications")
