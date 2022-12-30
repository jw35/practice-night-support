from django.shortcuts import redirect, render, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django.db.models import Count, F
from django.utils import timezone
from django.http import HttpResponseRedirect
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.conf import settings

from pprint import pprint
from datetime import datetime, timedelta

from .models import Event
from .forms import EventForm, CustomUserCreationForm, UserEditForm

import logging
logger = logging.getLogger(__name__)

# Create your views here.

from django.http import HttpResponse

def index(request):

    registration_form = CustomUserCreationForm()
    login_form = AuthenticationForm()
    event_list = None
    error_messages = []
    days = 14

    # Return from registering or logging in
    if request.method == 'POST':
      if 'login' in request.POST:
            login_form = AuthenticationForm(request.POST)
            username = request.POST.get('username')
            password = request.POST.get('password')
            user = authenticate(username=username, password=password)
            if user:
                if user.is_active:
                    login(request,user)
                    logger.info(f'"{user}" logged in')
                    return redirect(request.POST.get('next_page', settings.LOGIN_URL))
                else:
                    logger.info(f'Login attempt by suspended user "{user}"')
                    error_messages.append("Your account is suspended.")
            else:
                error_messages.append("Invalid login details")

      elif 'register' in request.POST:
            registration_form = CustomUserCreationForm(request.POST)
            if registration_form.is_valid():
                user = registration_form.save()
                login(request, user)
                logger.info(f'"{user}" registered and logged in')
                return redirect(request.POST.get('next_page', settings.LOGIN_URL))

    user = request.user

    if user.is_authenticated:

        try:
            days = int(request.GET.get('days', 14))
        except ValueError:
            days = 14

        event_list = (Event.objects.all()
                      .filter(start__gte=timezone.now())
                      .filter(start__lte=timezone.now()+timedelta(days=days))
                      .filter(cancelled=None)
                      .annotate(helpers_available=Count('helpers'))
                      .filter(helpers_required__gt=F("helpers_available"))
                      .order_by('start'))

    return render(request, "index.html",
        context={'events': event_list,
                 'days': days,
                 'login_form': login_form,
                 'registration_form': registration_form,
                 'error_messages': error_messages,
                 'next_page': request.GET.get('next')})


@login_required()
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


@login_required()
def event_details(request, event_id):
    event = get_object_or_404(Event, pk=event_id)

    user = request.user

    return render(request, "event.html",
        context={'event': event,
                 'user_is_owner': user == event.owner,
                 'user_is_helper': user in event.helpers.all()
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
def account(request):

    return render(request, "account.html")

@login_required()
def create_event(request):

    if request.method == 'POST':

        user = request.user

        form = EventForm(request.POST)

        if form.is_valid():

            duration = timedelta(hours=form.cleaned_data['hours'], minutes=form.cleaned_data['minutes'])

            event = Event.objects.create(start=form.cleaned_data['start'],
                                 duration=duration,
                                 location=form.cleaned_data['location'],
                                 helpers_required=form.cleaned_data['helpers_required'],
                                 owner=user)
            logger.info(f'Event id {event.id} "{event}" created by "{user}"')
            messages.success(request, 'Event successfully created')

            return HttpResponseRedirect(reverse('event-details', args=[event.pk]))

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
            errors.append('The request for help at this event has already been cancelled')

        if not errors and request.method == 'POST':
            if 'confirm' in request.POST:
                event.cancelled = timezone.now()
                event.save()

                logger.info(f'Event id {event.id} "{event}" cancelled by "{user}"')
                messages.success(request, 'The request for help at this event has been cancelled')

            return HttpResponseRedirect(reverse('event-details', args=[event.pk]))

    return render(request, 'cancel-event.html', {'event': event, 'errors': errors})

@login_required
def volunteer(request, event_id):

    with transaction.atomic():

        event = get_object_or_404(Event, pk=event_id)
        errors = []

        if event.past:
            errors.append('This event has already happened')
        elif event.cancelled:
            errors.append('The request for help at this event has been cancelled')

        user = request.user
        if user in event.helpers.all():
            errors.append('You have already volunteered to help at this event')

        if not errors and request.method == 'POST':
            if 'confirm' in request.POST:
                event.helpers.add(user)
                event.save()

                logger.info(f'"{user}" volunteered for event id {event.id} "{event}"')
                messages.success(request, 'You have been added as a helper for this event')

            return HttpResponseRedirect(reverse('event-details', args=[event.pk]))

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
            errors.append('You are not a helper for this event')

        if not errors and request.method == 'POST':
            if 'confirm' in request.POST:
                event.helpers.remove(request.user)
                event.save()

                logger.info(f'"{user}" un-volunteered for event id {event.id} "{event}"')
                messages.success(request, 'You are no longer a helper for this event')

            return HttpResponseRedirect(reverse('event-details', args=[event.pk]))

    return render(request, 'unvolunteer.html', {'event': event, 'errors': errors})

login_required()
def account_edit(request):

    user = request.user
    form = UserEditForm({'email': user.email, 'first_name': user.first_name, 'last_name': user.last_name, 'send_notifications': user.send_notifications})

    if request.method == 'POST':

        form = UserEditForm(request.POST)
        if form.is_valid():
            user.email = form.cleaned_data['email']
            user.first_name = form.cleaned_data['first_name']
            user.last_name = form.cleaned_data['last_name']
            user.send_notifications = form.cleaned_data['send_notifications']
            user.save()
            logger.info(f'"{user}" updated account details')
            messages.success(request, 'Your account details have been successfully updated')
            return HttpResponseRedirect(reverse('account'))

    return render(request, 'account-edit.html', {'form': form})


@login_required
def account_cancel(request):

    user = request.user
    errors = []

    with transaction.atomic():

        events_as_organiser = (Event.objects.all()
                               .filter(owner=user)
                               .filter(start__gte=timezone.now())
                               .filter(cancelled=None))

        events_as_volunteer = (Event.objects.all()
                               .filter(helpers=user)
                               .filter(start__gte=timezone.now())
                               .filter(cancelled=None))

        if events_as_organiser.all():
            errors.append('You are the organiser of events that have yet to happen.'
                          'You must cancel them or wait for them to happen before you can cancel your account.')
        if events_as_volunteer.all():
            errors.append('You are a helper for events that have yet to happen.'
                          'You must un-volunteer or wait for them to happen before you can cancel your account.')

        if user.is_superuser:
            errors.append("You have a superuser account. Superuser accounts can't be cancelled here.")

        if not errors and request.method == 'POST':
            if 'confirm' in request.POST:
                # Do this now before destroying user.first_name and user.last_name!
                log_message = f'"{user}" cancelled'
                user.cancelled = timezone.now()
                user.is_active = False
                user.set_unusable_password()
                user.email = f'canceled_{user.pk}'
                user.first_name = ''
                user.last_name = f'Cancelled user #{user.pk}'
                user.save()
                logout(request)
                logger.info(log_message)
                messages.success(request, 'Your account has been cancelled')
                return HttpResponseRedirect(reverse('index'))
            else:
                return HttpResponseRedirect(reverse('account'))

    return render(request, 'account-cancel.html',
                          {'errors': errors})
