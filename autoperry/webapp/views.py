from django.shortcuts import redirect, render, get_object_or_404
from django.contrib.auth import login
from django.urls import reverse
from webapp.forms import CustomUserCreationForm
from django.contrib.auth.decorators import login_required
from django.db.models import Count, F
from django.utils import timezone
from django.http import HttpResponseRedirect
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.db import transaction

from pprint import pprint
from datetime import datetime, timedelta

from .models import Event
from .forms import EventForm

# Create your views here.

from django.http import HttpResponse


def index(request):
    user = request.user

    event_list = (Event.objects.all()
                  .filter(start__gte=timezone.now())
                  .filter(start__lte=timezone.now()+timedelta(days=14))
                  .filter(cancelled=None)
                  .annotate(helpers_available=Count('helpers'))
                  .filter(helpers_required__gt=F("helpers_available"))
                  .order_by('start'))

    return render(request, "index.html", context={'events': event_list})

def register(request):
    if request.method == "GET":
        return render(
            request, "registration/register.html",
            {"form": CustomUserCreationForm}
        )
    elif request.method == "POST":
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect(reverse("index"))

def events(request):

    if 'past' in request.GET:
        if request.GET['past'] == 'y':
            request.session['include_past'] = True
        else:
            request.session['include_past'] = False
    elif 'include_past' not in request.session:
        request.session['include_past'] = False

    event_list = Event.objects.all().annotate(helpers_available=Count('volunteer')).order_by('start')

    if not request.session['include_past']:
        event_list = event_list.filter(start__gte=timezone.now())

    return render(request, "events.html",
        context={'events': event_list})


def event_details(request, event_id):
    event = get_object_or_404(Event, pk=event_id)

    user = request.user

    is_owner = user.is_authenticated and user == event.owner

    is_helper = user.is_authenticated and user in event.helpers.all()

    return render(request, "event.html",
        context={'event': event,
                 'user_is_owner': is_owner,
                 'user_is_helper': is_helper
                })

@login_required()
def my_events(request):

    user = request.user

    if 'past' in request.GET:
        if request.GET['past'] == 'y':
            request.session['include_past'] = True
        else:
            request.session['include_past'] = False
    elif 'include_past' not in request.session:
        request.session['include_past'] = False

    events_as_organiser = (Event.objects.all()
                           .filter(owner=user)
                           .annotate(helpers_available=Count('volunteer'))
                           .order_by('start'))

    if not request.session['include_past']:
        events_as_organiser = events_as_organiser.filter(start__gte=timezone.now())

    events_as_voluteer = (Event.objects.all()
                           .filter(helpers=user)
                           .annotate(helpers_available=Count('volunteer'))
                           .order_by('start'))

    if not request.session['include_past']:
        events_as_voluteer = events_as_voluteer.filter(start__gte=timezone.now())

    return render(request, "my-events.html",
                  context={ 'events_as_organiser': events_as_organiser,
                             'events_as_voluteer': events_as_voluteer})

@login_required()
def create_event(request):

    if request.method == 'POST':

        form = EventForm(request.POST)

        if form.is_valid():

            duration = timedelta(hours=form.cleaned_data['hours'], minutes=form.cleaned_data['minutes'])

            event = Event.objects.create(start=form.cleaned_data['start'],
                                 duration=duration,
                                 location=form.cleaned_data['location'],
                                 helpers_required=form.cleaned_data['helpers_required'],
                                 owner=request.user)
            messages.success(request, 'Event created')

            return HttpResponseRedirect(reverse('event_details', args=[event.pk]))

    else:
        form = EventForm()

    return render(request, 'create-event.html', {'form': form})

@login_required()
def cancel_event(request, event_id):

    with transaction.atomic():

        event = get_object_or_404(Event, pk=event_id)
        errors = []

        user = request.user
        if user != event.owner:
            errors.append('You are not the owner of this event')

        if event.past:
            errors.append('This event has already happened')
        elif event.cancelled:
            errors.append('This event has already been cancelled')

        if not errors and request.method == 'POST':
            event.cancelled = timezone.now()
            event.save()

            messages.success(request, 'Event cancelled')

            return HttpResponseRedirect(reverse('event_details', args=[event.pk]))

    return render(request, 'cancel-event.html', {'event': event, 'errors': errors})

@login_required
def volunteer(request, event_id):

    with transaction.atomic():

        event = get_object_or_404(Event, pk=event_id)
        errors = []

        if event.past:
            errors.append('This event has already happened')
        elif event.cancelled:
            errors.append('This event has been cancelled')

        user = request.user
        if user in event.helpers.all():
            errors.append('You have already volunteered to help at this event')

        if not errors and request.method == 'POST':
            if 'confirm' in request.POST:
                event.helpers.add(user)
                event.save()

                messages.success(request, 'You have been added as a volunteer for this event')

            return HttpResponseRedirect(reverse('event_details', args=[event.pk]))

    return render(request, 'volunteer.html', {'event': event, 'errors': errors})


@login_required
def unvolunteer(request, event_id):

    with transaction.atomic():

        event = get_object_or_404(Event, pk=event_id)
        errors = []

        if event.past:
            errors.append('This event has already happened')

        user = request.user
        if user not in event.helpers.all():
            errors.append('You are not a volunteer for this event')

        if not errors and request.method == 'POST':
            if 'confirm' in request.POST:
                event.helpers.remove(request.user)
                event.save()

                messages.success(request, 'You are no longer a volunteer for this event')

            return HttpResponseRedirect(reverse('event_details', args=[event.pk]))

    return render(request, 'unvolunteer.html', {'event': event, 'errors': errors})



