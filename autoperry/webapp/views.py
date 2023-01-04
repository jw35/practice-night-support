from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Count, F
from django.http import HttpResponseRedirect
from django.shortcuts import redirect, render, get_object_or_404
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils import timezone

from datetime import datetime, timedelta

from .models import Event
from .forms import EventForm, CustomUserCreationForm, UserEditForm

import logging
logger = logging.getLogger(__name__)

# Create your views here.

from django.http import HttpResponse

def index(request):

    login_form = AuthenticationForm()
    errors = []
    event_list = None
    days = 14

    # Return from registering or logging in
    if request.method == 'POST':
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
                errors.append('Your account is suspended - please contact <a href="mailto:autoperry@cambridgeringing.info">autoperry@cambridgeringing.info</a>')
        else:
            errors.append("Bad email address or password")

    user = request.user

    if user.is_authenticated:

        try:
            days = int(request.GET.get('days', 14))
        except ValueError:
            days = 14
        if days not in [14, 28, 56]:
            days=14

        event_list = (Event.objects.all()
                      .filter(start__gte=timezone.now())
                      .filter(start__lte=timezone.now()+timedelta(days=days))
                      .filter(cancelled=None)
                      .annotate(helpers_available=Count('helpers'))
                      .filter(helpers_required__gt=F("helpers_available"))
                      .order_by('start'))

    return render(request, "webapp/index.html",
        context={'events': event_list,
                 'days': days,
                 'login_form': login_form,
                 'errors': errors,
                 'next_page': request.GET.get('next')})

@login_required()
def events(request):

    user = request.user

    # Make search flags 'sticky', overridden by GET args
    if 'f' in request.GET:
        flags = {}
        for flag in ('past', 'cancelled', 'mine', 'location'):
            flags[flag] = flag in request.GET
    elif 'search_flags' in request.session:
        flags = request.session['search_flags']
    else:
        flags = {'past': False, 'cancelled': True, 'mine': False, 'location': False}
    request.session['search_flags'] = flags

    event_list = Event.objects.all().annotate(helpers_available=Count('volunteer'))

    if not flags['past']:
        event_list = event_list.filter(start__gte=timezone.now())

    if not flags['cancelled']:
        event_list = event_list.filter(cancelled=None)

    if flags['location']:
        event_list = event_list.order_by('location')
    else:
        event_list = event_list.order_by('start')

    events_as_organiser = event_list.filter(owner=user) if flags['mine'] else None
    events_as_voluteer = event_list.filter(helpers=user) if flags['mine'] else None

    paginator = Paginator(event_list, 20, orphans=2)
    paginator.ELLIPSIS = "X"
    try:
        page_number = int(request.GET.get('page'))
    except (ValueError, TypeError) as e:
        page_number = 1
    if page_number < 1 or page_number > paginator.num_pages:
        page_number = 1

    page_obj = paginator.get_page(page_number)
    page_range = paginator.get_elided_page_range(page_number, on_each_side=3, on_ends=1)

    return render(request, "webapp/events.html",
        context={'events': page_obj,
                 'page_range': page_range,
                 'events_as_organiser': events_as_organiser,
                 'events_as_voluteer': events_as_voluteer,
                 'flags': flags})


@login_required()
def event_details(request, event_id):
    event = get_object_or_404(Event, pk=event_id)

    user = request.user

    return render(request, "webapp/event.html",
        context={'event': event,
                 'user_is_owner': user == event.owner,
                 'user_is_helper': user in event.helpers.all()
                })


@login_required()
def account(request):

    return render(request, "webapp/account.html")

@login_required()
def event_create(request):

    user = request.user
    clashes = None

    if request.method == 'POST':

        form = EventForm(request.POST)

        if form.is_valid():

            date = form.cleaned_data.get("date")
            start_time = form.cleaned_data.get("start_time")
            end_time = form.cleaned_data.get("end_time")

            start = timezone.make_aware(datetime.combine(date, start_time))
            end = timezone.make_aware(datetime.combine(date, end_time))

            # Check for clashing events - test is (StartA <= EndB) and (EndA >= StartB)
            clashes = (Event.objects.all()
                       .filter(cancelled=None)
                       .filter(location=form.cleaned_data['location'])
                       .filter(start__lt=end)
                       .filter(end__gt=start))

                            # If there are, redisplay the form with a message
            if clashes.all():
                message = render_to_string("webapp/event_clash_error_fragment.html", { "location": form.cleaned_data['location'], "clashes": clashes })
                form.add_error(None, message)

            else:
                event = Event.objects.create(start=start,
                                     end=end,
                                     location=form.cleaned_data['location'],
                                     helpers_required=form.cleaned_data['helpers_required'],
                                     owner=user,
                                     contact_address=form.cleaned_data['contact_address'],
                                     notes=form.cleaned_data['notes'])
                logger.info(f'Event id {event.id} "{event}" created by "{user}"')
                messages.success(request, 'Event successfully created')

                return HttpResponseRedirect(reverse('event-details', args=[event.pk]))

    else:
        form = EventForm()

    # Get a list of Locations
    locations = Event.objects.filter(cancelled=None).values_list('location', flat=True).order_by('location').distinct()

    return render(request, 'webapp/event-create.html', {'form': form, 'locations': locations })

@login_required()
def event_clone(request, event_id):

    event = get_object_or_404(Event, pk=event_id)

    # Populate a new form from the event
    form =EventForm(initial=
        { 'date': event.start.date(),
          'start_time': event.start.time().strftime('%H:%M'),
          'end_time': event.end.time().strftime('%H:%M'),
          'location': event.location,
          'helpers_required': event.helpers_required,
          'contact_address': event.contact_address,
          'notes': event.notes})

    return render(request, 'webapp/event-create.html', {'form': form })

@login_required()
def event_edit(request, event_id):

    with transaction.atomic():

        event = get_object_or_404(Event, pk=event_id)
        errors = 0
        clashes = None
        form = None

        # Check if editing is actually possible

        user = request.user
        if user != event.owner:
            messages.error(request, 'You are not the owner of this event - only the owner can edit it.')
            errors += 1

        if len(event.helpers.all()) > 0:
            messages.error(request, "This event has helpers - details of events with helpers can't be edited. Consider cancelling it.")
            errors += 1

        if event.past:
            messages.error(request, "This event has already happened - events in the past can't be edited.")
            errors += 1
        elif event.cancelled:
            messages.error(request, "The request for help at this event has already been cancelled - cancelled events can't be edited.")
            errors == 1

        if errors:
            return HttpResponseRedirect(reverse('event-details', args=[event.pk]))

        # If the is a form submission
        if request.method == 'POST':

            form = EventForm(request.POST)

            if form.is_valid():

                date = form.cleaned_data.get("date")
                start_time = form.cleaned_data.get("start_time")
                end_time = form.cleaned_data.get("end_time")

                start = timezone.make_aware(datetime.combine(date, start_time))
                end = timezone.make_aware(datetime.combine(date, end_time))

                # Check for clashing events - test is (StartA <= EndB) and (EndA >= StartB)
                clashes = (Event.objects.all()
                           .exclude(pk=event.pk)
                           .filter(cancelled=None)
                           .filter(location=form.cleaned_data['location'])
                           .filter(start__lt=end)
                           .filter(end__gt=start))

                # If there are, redisplay the form with a message
                if clashes.all():
                    message = render_to_string("webapp/event_clash_error_fragment.html", { "location": form.cleaned_data['location'], "clashes": clashes })
                    form.add_error(None, message)

                # Otherwise success: update the event
                else:

                    event.start = start
                    event.end = end
                    event.location = form.cleaned_data['location']
                    event.helpers_required = form.cleaned_data['helpers_required']
                    event.contact_address = form.cleaned_data['contact_address']
                    event.notes = form.cleaned_data['notes']
                    event.save()
                    logger.info(f'Event id {event.id} "{event}" updated by "{user}"')
                    messages.success(request, 'Event successfully updated')

                    return HttpResponseRedirect(reverse('event-details', args=[event.pk]))

        # Otherwise populate the form
        else:

            form =EventForm(
            { 'date': event.start.date(),
              'start_time': event.start.time().strftime('%H:%M'),
              'end_time': event.end.time().strftime('%H:%M'),
              'location': event.location,
              'helpers_required': event.helpers_required,
              'contact_address': event.contact_address,
              'notes': event.notes})

    # Get a list of Locations
    locations = Event.objects.filter(cancelled=None).values_list('location', flat=True).order_by('location').distinct()

    # ... and display it
    return render(request, 'webapp/event-edit.html', {'form': form, 'locations': locations })


@login_required()
def event_cancel(request, event_id):

    with transaction.atomic():

        event = get_object_or_404(Event, pk=event_id)
        errors = 0

        user = request.user
        if user != event.owner:
            messages.error(request,'You are not the owner of this event - only the owner can cancel it')
            errors += 1

        if event.past:
            messages.error(request, "This event has already happened can so can't now be cancelled")
            errors += 1
        elif event.cancelled:
            messages.error(request, 'The request for help at this event has already been cancelled')
            errors += 1

        if not errors and request.method == 'POST':
            if 'confirm' in request.POST:
                event.cancelled = timezone.now()
                event.save()

                logger.info(f'Event id {event.id} "{event}" cancelled by "{user}"')

                for helper in event.helpers.all():
                    message = render_to_string("webapp/email/event_cancel_message.txt", { "event": event })
                    subject = render_to_string("webapp/email/event_cancel_subject.txt", { "event": event })
                    helper.email_user(subject, message)
                    # User.email_user doesn't return status information...
                    logger.info(f'Notified {user} that event id {event.id} "{event}" has been cancelled')

                messages.success(request, 'The request for help at this event has been cancelled')

            return HttpResponseRedirect(reverse('event-details', args=[event.pk]))

    return render(request, 'webapp/event-cancel.html', {'event': event, 'errors': errors})



@login_required
def volunteer(request, event_id):

    with transaction.atomic():

        user = request.user

        event = get_object_or_404(Event, pk=event_id)
        errors = 0

        if event.past:
            messages.error(request, "This event has already happened so you can't volunteer to help with it")
            errors += 1
        elif event.cancelled:
            messages.error(request, "The request for help at this event has been cancelled so you can't volunteer to help with it")
            errors += 1

        if user in event.helpers.all():
            messages.error(request, 'You have already volunteered to help at this event ')
            errors += 1

        # Check for clashing events - test is (StartA <= EndB) and (EndA >= StartB)
        clashes = (Event.objects.all()
                   .exclude(pk=event.pk)
                   .filter(cancelled=None)
                   .filter(helpers=user)
                   .filter(start__lt=event.end)
                   .filter(end__gt=event.start))

        # If there are, redisplay the form with a message
        if clashes.all():
            message = render_to_string("webapp/volunteer_clash_error_fragment.html", { "clashes": clashes })
            messages.error(request, message)
            errors += 1

        if not errors and request.method == 'POST':
            if 'confirm' in request.POST:
                event.helpers.add(user)
                event.save()

                logger.info(f'"{user}" volunteered for event id {event.id} "{event}"')
                messages.success(request, 'You have been added as a helper for this event')

            return HttpResponseRedirect(reverse('event-details', args=[event.pk]))

    return render(request, 'webapp/volunteer.html', {'event': event, 'errors': errors})


@login_required
def unvolunteer(request, event_id):

    with transaction.atomic():

        event = get_object_or_404(Event, pk=event_id)
        errors = 0

        if event.past:
            messages.error(request, "This event has already happened so you can't withdraw your offer to help")
            errors += 1

        user = request.user
        if user not in event.helpers.all():
            messages.error(request, "You are not already a helper for this event so you can't withdraw your offer to help")
            errors += 1

        if not errors and request.method == 'POST':
            if 'confirm' in request.POST:
                event.helpers.remove(request.user)
                event.save()

                logger.info(f'"{user}" un-volunteered for event id {event.id} "{event}"')
                messages.success(request, 'You are no longer a helper for this event')

            return HttpResponseRedirect(reverse('event-details', args=[event.pk]))

    return render(request, 'webapp/unvolunteer.html', {'event': event, 'errors': errors})

def account_create(request):

    registration_form = CustomUserCreationForm()

    # Return from registering or logging in
    if request.method == 'POST':
        registration_form = CustomUserCreationForm(request.POST)
        if registration_form.is_valid():
            user = registration_form.save()
            login(request, user)
            logger.info(f'"{user}" registered and logged in')
            return redirect(request.POST.get('next_page', settings.LOGIN_URL))

    return render(request, "webapp/account-create.html",
        context={'registration_form': registration_form})


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

    return render(request, 'webapp/account-edit.html', {'form': form})


@login_required
def account_cancel(request):

    user = request.user
    errors = 0

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
            messages.error(request, 'You are the organiser of events that have yet to happen. '
                          'You must cancel them or wait for them to happen before you can cancel your account.')
            errors += 1
        if events_as_volunteer.all():
            messages.error(request, 'You have volunteered to help with events that have yet to happen. '
                          'You must withdraw your offer or wait for them to happen before you can cancel your account.')
            errors += 1

        if user.is_superuser:
            messages.error(request, "You have a superuser account. Superuser accounts can't be cancelled here.")
            errors += 1

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

    return render(request, 'webapp/account-cancel.html',
                          {'errors': errors})
