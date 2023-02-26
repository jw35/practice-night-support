from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout, get_user_model
from django.contrib.auth.decorators import  permission_required
from django.contrib.auth.decorators import login_required as django_login_required
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.views import PasswordResetView as DefaultPasswordResetView
from django.core.exceptions import PermissionDenied
from django.core.mail import EmailMessage
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Count, F, Q
from django.http import HttpResponseRedirect, Http404
from django.shortcuts import redirect, render, get_object_or_404
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils import timezone
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.safestring import mark_safe

from datetime import datetime, timedelta
from uuid import uuid4

import ics
import pytz

from .models import Event
from .forms import EventForm, CustomUserCreationForm, UserEditForm, EmailForm
from .util import send_template_email, autoperry_login_required, EmailVerificationTokenGenerator, event_clash_error, volunteer_clash_error, build_stats_screen

import logging
logger = logging.getLogger(__name__)

# Create your views here.

from django.http import HttpResponse

def index(request):

    """
    Landing and login page
    """

    login_form = AuthenticationForm()
    errors = []
    event_list = None
    days = 14

    # Return from logging in
    if request.method == 'POST':
        login_form = AuthenticationForm(request.POST)
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(username=username, password=password)
        if user:
            login(request,user)
            logger.info(f'"{user}" logged in')
            return redirect(request.POST.get('next_page', settings.LOGIN_URL))
        else:
            errors.append("Bad email address or password")

    user = request.user

    # If they are still authenticated and enabled
    if user.is_authenticated and user.is_enabled:

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
                      .annotate(helpers_available=Count('volunteer', filter=(Q(volunteer__withdrawn=None) & Q(volunteer__declined=None))))
                      .filter(helpers_required__gt=F("helpers_available"))
                      .order_by('start', 'location'))

    # Always
    return render(request, "webapp/index.html",
        context={'events': event_list,
                 'days': days,
                 'login_form': login_form,
                 'errors': errors,
                 'next_page': request.GET.get('next')})


# ----------------------------------------------------------------------------------------
# Event Management
# ----------------------------------------------------------------------------------------

@autoperry_login_required()
def events(request):

    """
    List events
    """

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

    event_list = Event.objects.all().annotate(helpers_available=Count('volunteer', filter=(Q(volunteer__withdrawn=None) & Q(volunteer__declined=None))))

    if not flags['past']:
        event_list = event_list.filter(start__gte=timezone.now())

    if not flags['cancelled']:
        event_list = event_list.filter(cancelled=None)

    if flags['location']:
        event_list = event_list.order_by('location', 'start')
    else:
        event_list = event_list.order_by('start', 'location')

    events_as_organiser = event_list.filter(owner=user) if flags['mine'] else None
    events_as_voluteer = (event_list.filter(volunteer__person=user, volunteer__withdrawn=None, volunteer__declined=None)) if flags['mine'] else None

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


@autoperry_login_required()
def event_details(request, event_id):

    """
    Individual event details
    """

    event = get_object_or_404(Event, pk=event_id)

    user = request.user

    return render(request, "webapp/event.html",
        context={'event': event,
                 'user_is_owner': user == event.owner,
                 'user_is_helper': event.has_current_helper(user)
                })


@autoperry_login_required()
def event_create(request):

    """
    Create new event
    """

    user = request.user

    if request.method == 'POST':

        form = EventForm(request.POST)

        if form.is_valid():

            date = form.cleaned_data.get("date")
            start_time = form.cleaned_data.get("start_time")
            end_time = form.cleaned_data.get("end_time")

            start = datetime.combine(date, start_time)
            end = datetime.combine(date, end_time)

            message = event_clash_error(start, end, form.cleaned_data.get("location"))
            if message:
                form.add_error(None, message)
            else:
                event = Event.objects.create(start=start,
                                     end=end,
                                     location=form.cleaned_data['location'],
                                     helpers_required=form.cleaned_data['helpers_required'],
                                     owner=user,
                                     contact_address=form.cleaned_data['contact_address'],
                                     notes=form.cleaned_data['notes'],
                                     alerts=form.cleaned_data['alerts'])
                logger.info(f'Event id {event.id} "{event}" created by "{user}"')
                messages.success(request, 'Event successfully created')

                return HttpResponseRedirect(reverse('event-details', args=[event.pk]))

    else:
        form = EventForm()

    # Get a list of Locations
    locations = Event.objects.filter(cancelled=None).values_list('location', flat=True).order_by('location').distinct()

    return render(request, 'webapp/event-create.html', {'form': form, 'locations': locations })


@autoperry_login_required()
def event_clone(request, event_id):

    """
    Create new event based on existing one
    """

    event = get_object_or_404(Event, pk=event_id)

    # Populate a new form from the event
    form =EventForm(initial=
        { 'date': event.start.date(),
          'start_time': event.start.time().strftime('%H:%M'),
          'end_time': event.end.time().strftime('%H:%M'),
          'location': event.location,
          'helpers_required': event.helpers_required,
          'contact_address': event.contact_address,
          'notes': event.notes,
          'alerts': event.alerts})

    # Get a list of Locations
    locations = (Event.objects
        .filter(cancelled=None)
        .values_list('location', flat=True)
        .order_by('location')
        .distinct())

    return render(request, 'webapp/event-create.html', {'form': form, 'locations': locations })


@autoperry_login_required()
def event_edit(request, event_id):

    """
    Edit existing event
    """

    with transaction.atomic():

        event = get_object_or_404(Event, pk=event_id)

        initial_data = { 'date': event.start.date(),
              'start_time': event.start.time(),
              'end_time': event.end.time(),
              'location': event.location,
              'helpers_required': event.helpers_required,
              'contact_address': event.contact_address,
              'notes': event.notes,
              'alerts': event.alerts }

        errors = 0
        form = None

        # Check if editing is actually possible

        user = request.user
        if user != event.owner:
            messages.error(request, 'You are not the owner of this event - only the owner can edit it.')
            errors += 1
        elif event.past:
            messages.error(request, "This event has already happened - events in the past can't be edited.")
            errors += 1
        elif event.cancelled:
            messages.error(request, "The request for help at this event has been cancelled - cancelled events can't be edited.")
            errors += 1

        if errors:
            return HttpResponseRedirect(reverse('event-details', args=[event.pk]))

        # If the is a form submission
        if request.method == 'POST':

            form = EventForm(request.POST, initial=initial_data)

            if form.is_valid():

                date = form.cleaned_data.get("date")
                start_time = form.cleaned_data.get("start_time")
                end_time = form.cleaned_data.get("end_time")

                start = datetime.combine(date, start_time)
                end = datetime.combine(date, end_time)

                # If there are clashes, redisplay the form with a message
                message = event_clash_error(start, end, form.cleaned_data.get("location"), this=event)
                if message:
                    form.add_error(None, message)
                # Otherwise success: update the event
                else:

                    if form.has_changed():
                        event.start = start
                        event.end = end
                        event.location = form.cleaned_data['location']
                        event.helpers_required = form.cleaned_data['helpers_required']
                        event.contact_address = form.cleaned_data['contact_address']
                        event.notes = form.cleaned_data['notes']
                        event.alerts = form.cleaned_data['alerts']
                        event.save()

                        logger.info(f'Event id {event.id} "{event}" updated by "{user}"')

                        send_email = False
                        for field in ('date', 'start_time', 'end_time', 'location', 'helpers_required', 'notes'):
                            if initial_data[field] != form.cleaned_data[field]:
                                send_email = True

                        if send_email:
                            for helper in event.current_helpers:
                                if helper.send_notifications:
                                    send_template_email(helper, "event-edit",
                                        { "event": event, "before": initial_data,
                                          "after": form.cleaned_data })
                                else:
                                    logger.warn(f'Unable to notify {helper} that event id {event.id} "{event}" has been edited')
                        else:
                            logger.info(f'No emailable changes to Event id {event.id} "{event}"')


                        messages.success(request, 'Event successfully updated')

                    else:
                        logger.info(f'Event id {event.id} "{event}" unchanged by "{user}"')
                        messages.success(request, 'No change made to the event')

                    return HttpResponseRedirect(reverse('event-details', args=[event.pk]))

        # Otherwise populate the form
        else:

            form =EventForm(initial_data)

    # Get a list of Locations
    locations = (Event.objects
        .filter(cancelled=None)
        .values_list('location', flat=True)
        .order_by('location')
        .distinct())

    # ... and display it
    return render(request, 'webapp/event-edit.html',
        {'form': form,
          'locations': locations,
          'event': event })


@autoperry_login_required()
def event_cancel(request, event_id):

    """
    Cancel (request for help at) an event
    """

    with transaction.atomic():

        event = get_object_or_404(Event, pk=event_id)
        errors = 0

        user = request.user

        if user != event.owner:
            messages.error(request,'You are not the owner of this event - only the owner can cancel it')
            errors += 1
        elif event.past:
            messages.error(request, "This event has already happened can so can't now be cancelled")
            errors += 1
        elif event.cancelled:
            messages.error(request, 'The request for help at this event has already been cancelled')
            errors += 1

        if errors:
            return HttpResponseRedirect(reverse('event-details', args=[event.pk]))

        if request.method == 'POST':
            if 'confirm' in request.POST:
                event.cancelled = timezone.now()
                event.save()

                logger.info(f'Event id {event.id} "{event}" cancelled by "{user}"')

                for helper in event.current_helpers:
                    if helper.send_notifications:
                        send_template_email(helper, "event-cancel", { "event": event })
                    else:
                        logger.info(f'Unable to notify {helper} that event id {event.id} "{event}" has been cancelled')

                messages.success(request, 'Event cancelled')

            return HttpResponseRedirect(reverse('event-details', args=[event.pk]))

    return render(request, 'webapp/event-cancel.html', {'event': event})


# ----------------------------------------------------------------------------------------
# Helper Management
# ----------------------------------------------------------------------------------------

@autoperry_login_required
def volunteer(request, event_id):

    """
    Add current user as helper
    """

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
        elif event.has_current_helper(user):
            messages.error(request, 'You have already volunteered to help at this event ')
            errors += 1
        elif not event.helpers_needed:
            messages.error(request, "This event already has enough helpers so you can't also volunteer to help with it")
            errors += 1

        # Check for clashing events - test is (StartA <= EndB) and (EndA >= StartB)
        message =volunteer_clash_error(user, event)
        if message:
            messages.error(request, message)
            errors += 1

        if errors:
            return HttpResponseRedirect(reverse('event-details', args=[event.pk]))

        if request.method == 'POST':
            if 'confirm' in request.POST:
                event.volunteer_set.create(person=user)

                logger.info(f'"{user}" volunteered for event id {event.id} "{event}"')
                messages.success(request, 'You have been added as a helper for this event')

                if event.alerts and event.owner.send_notifications:
                    send_template_email(event.owner, "volunteer", { "event": event, "helper": user })

            return HttpResponseRedirect(reverse('event-details', args=[event.pk]))

    return render(request, 'webapp/volunteer.html', {'event': event})


@autoperry_login_required
def unvolunteer(request, event_id):

    """
    REmove current user as helper
    """

    with transaction.atomic():

        event = get_object_or_404(Event, pk=event_id)
        errors = 0

        user = request.user

        if event.past:
            messages.error(request, "This event has already happened so you can't withdraw your offer to help")
            errors += 1
        elif not event.has_current_helper(user):
            messages.error(request, "You are not a helper for this event so you can't withdraw your offer to help")
            errors += 1

        if errors:
            return HttpResponseRedirect(reverse('event-details', args=[event.pk]))

        if request.method == 'POST':
            if 'confirm' in request.POST:
                volunteer = event.volunteer_set.get(person=user, withdrawn=None, declined=None)
                volunteer.withdrawn = timezone.now()
                volunteer.save()

                logger.info(f'"{user}" un-volunteered for event id {event.id} "{event}"')
                messages.success(request, 'You are no longer a helper for this event')

                if event.alerts and event.owner.send_notifications:
                    send_template_email(event.owner, "unvolunteer", { "event": event, "helper": user })

            return HttpResponseRedirect(reverse('event-details', args=[event.pk]))

    return render(request, 'webapp/unvolunteer.html', {'event': event})


@autoperry_login_required
def decline(request, event_id, helper_id):

    with transaction.atomic():

        event = get_object_or_404(Event, pk=event_id)
        helper = get_object_or_404(get_user_model(), pk=helper_id)
        errors = 0

        user = request.user

        if event.past:
            messages.error(request, "This event has already happened so you can't decline an offer to help")
            errors += 1
        elif user != event.owner:
            messages.error(request,'You are not the owner of this event - only the owner can decline offers of help')
            errors += 1
        elif not event.has_current_helper(helper):
            messages.error(request, f"{helper} is not a helper for this event so you can't decline their offer to help")
            errors += 1

        if errors:
            return HttpResponseRedirect(reverse('event-details', args=[event.pk]))

        if request.method == 'POST':
            if 'confirm' in request.POST:
                volunteer = event.volunteer_set.get(person=helper, withdrawn=None, declined=None)
                volunteer.declined = timezone.now()
                volunteer.save()

                logger.info(f'"{user}" declined {helper} as helper for event id {event.id} "{event}"')
                messages.success(request, f'{helper} as been removed as a helper')

                if helper.send_notifications:
                    send_template_email(helper, "helper-declined", { "event": event })

            return HttpResponseRedirect(reverse('event-details', args=[event.pk]))

    return render(request, 'webapp/decline.html', {'event': event, 'helper': helper})


# ----------------------------------------------------------------------------------------
# Account Management
# ----------------------------------------------------------------------------------------

@autoperry_login_required
@permission_required('custom_user.administrator', raise_exception=True)
def account_list(request):

    """
    List accounts (admin only)
    """

    # Make search flags 'sticky', overridden by GET args
    if 'f' in request.GET:
        flags = {}
        for flag in ('pending', 'current', 'suspended', 'cancelled'):
            flags[flag] = flag in request.GET
    elif 'user_flags' in request.session:
        flags = request.session['user_flags']
    else:
        flags = {'pending': True, 'current': True, 'suspended': True, 'cancelled': False}
    request.session['user_flags'] = flags

    base_users = get_user_model().objects.all()

    users = get_user_model().objects.none()

    if flags['pending']:
        u = base_users.filter(email_validated=None) | base_users.filter(approved=None)
        u = u.filter(suspended=None).filter(cancelled=None)
        users = users | u

    if flags['current']:
        users = users | (base_users.exclude(email_validated=None)
            .exclude(approved=None)
            .filter(suspended=None)
            .filter(cancelled=None))

    if flags['suspended']:
        users = users | base_users.exclude(suspended=None)

    if flags['cancelled']:
        users = users | base_users.exclude(cancelled=None)

    users = (users
        .annotate(num_owned=Count('events_owned', distinct=True))
        .annotate(num_helped=Count('volunteer__id', filter=(Q(volunteer__withdrawn=None) & Q(volunteer__declined=None)), distinct=True))
    )

    users = users.order_by('last_name', 'first_name')

    paginator = Paginator(users, 20, orphans=2)
    paginator.ELLIPSIS = "X"
    try:
        page_number = int(request.GET.get('page'))
    except (ValueError, TypeError) as e:
        page_number = 1
    if page_number < 1 or page_number > paginator.num_pages:
        page_number = 1

    page_obj = paginator.get_page(page_number)
    page_range = paginator.get_elided_page_range(page_number, on_each_side=3, on_ends=1)

    return render(request, "webapp/account-list.html",
        context={'users': page_obj,
                 'page_range': page_range,
                 'flags': flags})


@django_login_required()
def account(request):

    """
    Individual account details
    """

    user = request.user
    if not user.uuid:
        user.uuid = uuid4()
        user.save()

    return render(request, "webapp/account.html")


def account_create(request):

    """
    Create a new account
    """

    registration_form = CustomUserCreationForm()

    # Return from registering or logging in
    if request.method == 'POST':
        registration_form = CustomUserCreationForm(request.POST)
        if registration_form.is_valid():
            user = registration_form.save()
            login(request, user)

            logger.info(f'Created new user "{user}"')

            # Email verification
            email_verification_token = EmailVerificationTokenGenerator()

            send_template_email(user, "email-validate", {
                'email': user.email,
                'uid': urlsafe_base64_encode(force_bytes(user.pk)),
                'token': email_verification_token.make_token(user)
                }, force=True)

            # Alert the admins
            send_template_email(settings.DEFAULT_FROM_EMAIL, "account-approval-required",
                { 'user': user })

            return render(request, "webapp/account-create-pending.html",
                context={'sender': settings.DEFAULT_FROM_EMAIL,
                         'uid': urlsafe_base64_encode(force_bytes(user.pk)),
                         'user': user })

    return render(request, "webapp/account-create.html",
        context={'registration_form': registration_form})


@django_login_required
def account_resend(request):

    """
    Resend email validation request
    """

    user = request.user

    if user.email_validated:
        messages.success(request, 'This email address has already been confirmed')
        return redirect(reverse('index'))

    email_verification_token = EmailVerificationTokenGenerator()

    send_template_email(user, "email-validate", {
        'email': user.email,
        'uid': urlsafe_base64_encode(force_bytes(user.pk)),
        'token': email_verification_token.make_token(user)
        }, force=True)

    messages.success(request, 'Email resent')
    logger.info(f'Resent validation request for "{user}" to {user.email}')

    return render(request, "webapp/account-create-resend.html",
        context={'sender': settings.DEFAULT_FROM_EMAIL,
                 'user': user })


def account_confirm(request, uidb64, token):

    """
    Receive email confirmation
    """

    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = get_user_model().objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, get_user_model().DoesNotExist):
        raise Http404;

    email_verification_token = EmailVerificationTokenGenerator()

    if user.email_validated:
        messages.success(request, 'This email address has already been confirmed')
    elif email_verification_token.check_token(user, token):
        user.email_validated = timezone.now()
        user.save()
        logger.info(f'"{user}" email verified')
        if user.approved:
            messages.success(request, 'Your email address has been confirmed and you can login in.')
        else:
            messages.warning(request, 'Your email address has been confirmed, but your account has yet to be approved.')
    else:
        messages.success(request, 'Email address verification failed')
        logger.error(f'"{user}" email verification failed')

    return redirect(reverse('index'))


@django_login_required()
def account_edit(request):

    """
    Edit existing account
    """

    with transaction.atomic():

        user = request.user
        form = UserEditForm(
            {'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'tower': user.tower,
            'send_notifications': user.send_notifications,
            'send_other': user.send_other,
            })

        if request.method == 'POST':

            original_email = user.email

            form = UserEditForm(request.POST)
            if form.is_valid():
                user.email = form.cleaned_data['email']
                user.first_name = form.cleaned_data['first_name']
                user.last_name = form.cleaned_data['last_name']
                user.tower = form.cleaned_data['tower']
                user.send_notifications = form.cleaned_data['send_notifications']
                user.send_other = form.cleaned_data['send_other']
                user.save()
                logger.info(f'"{user}" updated account details')

                messages.success(request, 'Your account details have been successfully updated')

                if user.email != original_email:
                    user.email_validated =  None;
                    user.save()
                    logout(request)

                    email_verification_token = EmailVerificationTokenGenerator()
                    send_template_email(user, "email-validate", {
                        'email': user.email,
                        'uid': urlsafe_base64_encode(force_bytes(user.pk)),
                        'token': email_verification_token.make_token(user)
                        }, force=True)
                    return render(request, "webapp/account-create-resend.html",
                        context={'sender': settings.DEFAULT_FROM_EMAIL,
                                 'user': user })

                return HttpResponseRedirect(reverse('account'))

    return render(request, 'webapp/account-edit.html', {'form': form})


@django_login_required
def account_cancel(request):

    """
    Cancel existing account
    """

    user = request.user
    errors = 0

    with transaction.atomic():

        events_as_organiser = (Event.objects.all()
                               .filter(owner=user)
                               .filter(start__gte=timezone.now())
                               .filter(cancelled=None))

        events_as_volunteer = (Event.objects.all()
                               .filter(volunteer__person=user, volunteer__withdrawn=None, volunteer__declined=None)
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

        if errors:
            return HttpResponseRedirect(reverse('account'))

        if request.method == 'POST':
            if 'confirm' in request.POST:
                # Do this now before destroying user.first_name and user.last_name!
                log_message = f'"{user}" cancelled'
                user.cancelled = timezone.now()
                user.is_active = False
                user.set_unusable_password()
                user.email = f'canceled_{user.pk}'
                user.first_name = ''
                user.last_name = f'Cancelled user #{user.pk}'
                user.tower = ''
                user.send_notifications = False
                user.send_other = False
                user.save()
                logout(request)
                logger.info(log_message)
                messages.success(request, 'Your account has been cancelled')
                return HttpResponseRedirect(reverse('index'))
            else:
                return HttpResponseRedirect(reverse('account'))

    return render(request, 'webapp/account-cancel.html')


@autoperry_login_required
@permission_required('custom_user.administrator', raise_exception=True)
def account_approve_list(request):

    """
    List users requiring approval
    """

    users = (get_user_model().objects.all()
        .filter(approved=None)
        .filter(cancelled=None)
        .filter(suspended=None)
        .order_by('date_joined'))

    return render(request, 'webapp/account-approve-list.html', {'users': users})


@autoperry_login_required
@permission_required('custom_user.administrator', raise_exception=True)
def account_approve(request, user_id):

    user = get_object_or_404(get_user_model(), pk=user_id)

    errors = 0
    if user.approved:
        messages.error(request,f'User {user} has already been approved')
        errors += 1

    else:

        with transaction.atomic():

            if request.method == 'POST':

                user.approved = timezone.now()
                user.save()

                send_template_email(user, "account-approved", { 'user': user }, force=True)

                logger.info(f'"{user}" approved by "{request.user}"')
                messages.success(request, f'Account for {user} approved')

                return HttpResponseRedirect(reverse('account-approve-list'))

    return render(request, 'webapp/account-approve.html',
        { 'candidate': user,
          'errors': errors })


@autoperry_login_required
@permission_required('custom_user.administrator', raise_exception=True)
def account_toggle(request, action, user_id):

    user = get_object_or_404(get_user_model(), pk=user_id)

    errors = 0
    if action == 'suspend' and user.suspended:
        messages.error(request,f'User {user} is already suspended')
        errors += 1
    elif action == 'enable' and not user.suspended:
        messages.error(request,f'User {user} is already enabled')
        errors += 1

    else:
        with transaction.atomic():

            if request.method == 'POST':

                if action == 'enable':
                    user.suspended = None
                    logger.info(f'"{user}" re-enabled by "{request.user}"')
                    messages.success(request, f'Account for {user} re-enabled')
                elif action == 'suspend':
                    user.suspended = timezone.now()
                    logger.info(f'"{user}" suspended by "{request.user}"')
                    messages.success(request, f'Account for {user} suspended')

                user.save()

                return HttpResponseRedirect(reverse('account-list'))

    return render(request, 'webapp/account-toggle.html',
        { 'user': user, 'action': action, 'errors': errors })


@autoperry_login_required
@permission_required('custom_user.administrator', raise_exception=True)
def send_emails(request):

    """
    Send bulk email (admin only)
    """

    form = EmailForm();

    if request.method == 'POST':

        form = EmailForm(request.POST)
        if form.is_valid():

            base_users = (get_user_model().objects.all()
                .filter(cancelled=None)
                .exclude(email_validated=None)
                .filter(send_other=True)
                .annotate(num_owned=Count('events_owned', distinct=True))
                .annotate(num_helped=Count('volunteer__person', filter=(Q(volunteer__withdrawn=None) & Q(volunteer__declined=None)), distinct=True))
            )

            users = get_user_model().objects.none()

            if form.cleaned_data['helpers']:
                users = users | base_users.filter(num_helped__gt=0)

            if form.cleaned_data['organisers']:
                users = users | base_users.filter(num_owned__gt=0)

            if form.cleaned_data['rest']:
                users = users | base_users.filter(num_helped__exact=0).filter(num_owned__exact=0)

            to_addresses = users.values_list('email', flat=True)

            print(to_addresses)

            if to_addresses:

                template = 'email-email'
                context = { 'subject': form.cleaned_data['subject'], 'message': form.cleaned_data['message'] }
                message = render_to_string(f"webapp/email/{template}-message.txt", context).strip()
                subject = render_to_string(f"webapp/email/{template}-subject.txt", context).strip()

                EmailMessage(subject=subject,
                    body=message,
                    bcc=to_addresses,
                    cc=(settings.DEFAULT_FROM_EMAIL,)).send()

                messages.success(request, f'Bulk email sent to {len(to_addresses)} addresses')
                logger.info(f'Email sent to {len(to_addresses)} addresses')
                form = EmailForm();

            else:
                messages.error(request,'No users would be emailed by this selection!')

    return render(request, "webapp/send-email.html", {'form': form})


class PasswordResetView(DefaultPasswordResetView):
    """
    Override protocol as sent to message template to use our configuration
    """
    extra_email_context = { 'protocol': settings.WEBAPP_SCHEME }


@autoperry_login_required()
def stats_screen(request):

    """
    Stats summary
    """

    return render(request, "webapp/stats-screen.html",
        context=build_stats_screen(timezone.now())
        )

def ical(request, uuid):

    user = get_object_or_404(get_user_model(), uuid=uuid)

    event_list = Event.objects.all().filter(start__gte=timezone.now()).filter(cancelled=None)

    events_as_organiser = event_list.filter(owner=user)
    events_as_voluteer = (event_list.filter(volunteer__person=user, volunteer__withdrawn=None, volunteer__declined=None))

    c = ics.Calendar()
    c.creator = f'AutoPerry - {settings.WEBAPP_SCHEME}://{settings.WEBAPP_DOMAIN}/'
    tz = pytz.timezone('Europe/London')

    for event in events_as_voluteer:
        e = ics.Event(
          name = "AutoPerry helper",
          description = event.notes,
          begin = event.start.replace(tzinfo=tz),
          end = event.end.replace(tzinfo=tz),
          location = event.location,
          organizer = event.contact,
          url = f"{settings.WEBAPP_SCHEME}://{settings.WEBAPP_DOMAIN}{event.get_absolute_url()}",
          uid = f"helper-{event.pk}@autoperry.cambridgeringing.org"
        )
        c.events.add(e)

    for event in events_as_organiser:
        e = ics.Event(
          name = "AutoPerry event",
          description=event.notes,
          begin = event.start.replace(tzinfo=tz),
          end = event.end.replace(tzinfo=tz),
          location = event.location,
          url = f"{settings.WEBAPP_SCHEME}://{settings.WEBAPP_DOMAIN}{event.get_absolute_url()}",
          uid = f"organizer-{event.pk}@autoperry.cambridgeringing.org"
        )
        c.events.add(e)

    response = HttpResponse(
        content_type='text/calendar',
        headers={'Content-Disposition': 'attachment; filename="autoperry.ics"'},
    )

    response.writelines(c.serialize_iter())

    logger.info(f'Calendar feed collected by "{user}"')

    return response
