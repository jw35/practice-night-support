# webapp/forms.py

from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import get_user_model
from django import forms
from django.utils import timezone
from django.core.exceptions import ValidationError

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit, Row, Column

from datetime import date, time, datetime, timedelta

class CustomUserCreationForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        fields = list(UserCreationForm.Meta.fields) + ["email", "first_name", "last_name", "tower", "send_notifications", "send_other"]
        fields.remove("username")
        model = get_user_model()


def today_or_tomorrow():
    """
    Return tomorrows date if it's past 19:30, else todays date
    """
    now = datetime.now()
    if now.time() > time(hour=19, minute=30):
        return (now + timedelta(days=1)).date()
    return now.date()

class EventForm(forms.Form):
    date = forms.DateField(help_text='Event date', initial=today_or_tomorrow, widget=forms.widgets.DateInput(attrs={'type': 'date'}))
    start_time = forms.TimeField(help_text='Event start time', initial="19:30", widget=forms.widgets.DateInput(format="%H:%M", attrs={'type': 'time', 'step': 300}))
    end_time = forms.TimeField(help_text='Event finish time', initial="21:00", widget=forms.widgets.DateInput(format="%H:%M", attrs={'type': 'time', 'step': 300}))
    location = forms.CharField(max_length=60, help_text='Where the event takes place')
    helpers_required = forms.IntegerField(min_value=1, label='Helpers wanted', help_text='Number of helpers wanted', initial=1)
    contact_address = forms.CharField(max_length=60, required=False, help_text="Email address for the event (yours if blank)")
    notes = forms.CharField(max_length=200, required=False, help_text="Purpose of the event, helper skills required, etc. (optional, max 200 chars.)")
    alerts = forms.BooleanField(required=False, label="Send emails when helpers change")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_tag = False
        self.helper.layout = Layout(
            Row(
                Column('date', css_class='form-group col-md-4 mb-0'),
                Column('start_time', css_class='form-group col-md-4 mb-0'),
                Column('end_time', css_class='form-group col-md-4 mb-0'),
                css_class='form-row'
            ),
            Row(
                Column('location', css_class='form-group col-md-8 mb-0'),
                Column('helpers_required', css_class='form-group col-md-4 mb-0'),
                css_class='form-row'
            ),
            'contact_address',
            'notes',
            'alerts'
        )

    def clean(self):
        cleaned_data = super().clean()
        date = cleaned_data.get("date")
        start_time = cleaned_data.get("start_time")
        end_time = cleaned_data.get("end_time")

        if date and start_time and end_time:

            if start_time >= end_time:
                raise ValidationError("End time must be later than start time!")

            start = datetime.combine(date, start_time)
            if start < timezone.now():
                raise ValidationError("Event start is in the past. Events must start in the future!")

    class Media:
        css = {
            'all': ('webapp/jquery-ui.min.css',)
        }
        js = ('webapp/jquery.min.js', 'webapp/jquery-ui.min.js')

class UserEditForm(forms.Form):
    email = forms.EmailField(help_text="You will need to re-confirm your email address if you change this")
    first_name = forms.CharField(max_length=150)
    last_name = forms.CharField(max_length=150)
    tower = forms.CharField(max_length=50, help_text="Where do you normally ring")
    send_notifications = forms.BooleanField(required=False, label="Send email alerts and reminders about your events")
    send_other = forms.BooleanField(required=False, label="Send other emails")

class EmailForm(forms.Form):
    helpers = forms.BooleanField(required=False, initial=True, label="Include helpers?")
    organisers = forms.BooleanField(required=False, initial=True, label="Include organisers?")
    rest = forms.BooleanField(required=False, initial=True, label="Include others?")
    subject = forms.CharField(required=True)
    message = forms.CharField(required=True, widget=forms.Textarea)



