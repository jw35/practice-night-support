from django.conf import settings
from django.contrib.auth import get_user_model

from django.core.mail import send_mail
from django.contrib.auth.decorators import user_passes_test
from django.contrib.auth import REDIRECT_FIELD_NAME
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.contrib.sites.shortcuts import get_current_site
from django.db.models import Q, Count, Sum
from django.db.models.functions import TruncMonth
from django.template.loader import render_to_string

from custom_user.models import User
from .models import Event

import logging
logger = logging.getLogger(__name__)

def send_template_email(to,template,context,force=False):

    """
    Construct an email from the supplied template path and context
    and send it to the user
    """

    local_context = context.copy()
    local_context['domain'] = settings.WEBAPP_DOMAIN
    local_context['scheme'] = settings.WEBAPP_SCHEME

    message = render_to_string(f"webapp/email/{template}-message.txt", local_context).strip()
    subject = render_to_string(f"webapp/email/{template}-subject.txt", local_context).strip()

    if isinstance(to, User):

        # If 'to' us a user, don't send to cancelled or suspended users, and don't
        # send unless the user approved 'notification' emails or force if True

        if to.cancelled or to.suspended:
            logger.warn(f'Not emailing {to} "{subject}" - user cancelled or suspended')
            return
        if not to.email_validated and not force:
            logger.warn(f'Not emailing {to} "{subject}" - email not yet validated')
            return
        if not to.send_notifications and not force:
            logger.warn(f'Not emailing {to} "{subject}" - notifications not wanted')
            return
        to.email_user(subject, message)
        logger.info(f'Emailed user {to} {to.email} "{subject}"')

    else:

        send_mail(subject, message, None, [to])
        logger.info(f'Emailed address {to} "{subject}"')


def autoperry_login_required(function=None, redirect_field_name=REDIRECT_FIELD_NAME, login_url=None):

    """
    Copy of login_required from django.contrib.auth.decorators with condition
    expanded to include email_validated and not suspended
    """

    actual_decorator = user_passes_test(
        lambda u: (u.is_authenticated and u.is_enabled),
        login_url=login_url,
        redirect_field_name=redirect_field_name,
    )
    if function:
        return actual_decorator(function)
    return actual_decorator

class EmailVerificationTokenGenerator(PasswordResetTokenGenerator):

    """
    MAke a customised hash that includes user.email_validated
    """
    def _make_hash_value(self, user, timestamp):
        return (
                str(user.email_validated) + str(user.pk) + str(timestamp)
        )


def event_clash_error(start, end, location):

    """
    Test if adding and event from start to end at location
    would clash with an existing event. Return an error message
    if so, else None
    """

    clashes = (Event.objects.all()
                .filter(cancelled=None)
                .filter(location=location)
                .filter(start__lt=end)
                .filter(end__gt=start))

    if clashes.all():
        message = (render_to_string("webapp/event-clash-error-fragment.html",
            { "clashes": clashes }))
        return message

    return None


def volunteer_clash_error(user, event):

    """
    Test if user volunteering to help at event
    would clash with their other volunteering commitments.
    Return an error message if so, else None
    """

    clashes = (Event.objects.all()
               .exclude(pk=event.pk)
               .filter(cancelled=None)
               .filter(helpers=user)
               .filter(start__lt=event.end)
               .filter(end__gt=event.start))

    if clashes.all():
        message = render_to_string("webapp/volunteer-clash-error-fragment.html",
            { "clashes": clashes })
        return message

    return None

def build_stats_screen(now):

    """
    Collect aggregate statistics for the stats page
    """

    people_totals = (get_user_model().objects.all()
        .aggregate(
            pending=Count('id', filter=(Q(approved=None) | Q(email_validated=None)) & Q(cancelled=None) & Q(suspended=None)),
            live=Count('id', filter=(~Q(approved=None) & ~Q(email_validated=None)) & Q(cancelled=None) & Q(suspended=None)),
            suspended=Count('id', filter=Q(cancelled=None) & ~Q(suspended=None)),
            cancelled=Count('id', filter=(~Q(cancelled=None)))
        )
    )

    event_totals = (Event.objects.all()
        .filter(start__lte=now)
        .aggregate(
            events=Count('id', filter=Q(cancelled=None)),
            cancelled_events=Count('id', filter=~Q(cancelled=None)),
            owners=Count('owner', distinct=True, filter=Q(cancelled=None)),
            locations=Count('location', distinct=True, filter=Q(cancelled=None)),
            helpers_wanted=Sum('helpers_required', filter=Q(cancelled=None)),
        )
    )

    helper_totals = (Event.objects.all()
        .filter(start__lte=now)
        .aggregate(
            helpers_provided=Count('helpers', filter=Q(cancelled=None)),
            distinct_helpers=Count('helpers', distinct=True, filter=Q(cancelled=None)),
            helpers_cancelled=Count('helpers', filter=~Q(cancelled=None))
        )
    )

    print(event_totals, helper_totals)

    events = (Event.objects.all()
        .filter(start__lte=now)
        .annotate(month=TruncMonth('start'))
        .values('month')
    )

    event_sum = (events
        .annotate(
            events=Count('id', filter=Q(cancelled=None)),
            cancelled_events=Count('id', filter=~Q(cancelled=None)),
            owners=Count('owner', distinct=True, filter=Q(cancelled=None)),
            locations=Count('location', distinct=True, filter=Q(cancelled=None)),
            helpers_wanted=Sum('helpers_required', filter=Q(cancelled=None))
        )
        .order_by()
    )

    # Have to count helpers in a separate query because it introduces
    # a join which would multiply counts on Event fields
    helper_sum = (events
        .annotate(
            helpers_provided=Count('helpers', filter=Q(cancelled=None)),
            distinct_helpers=Count('helpers', distinct=True, filter=Q(cancelled=None)),
            helpers_cancelled=Count('helpers', filter=~Q(cancelled=None))
        )
        .order_by()
    )

    # The two queries should return results for the same months in the
    # same order so we can zip them together and return them. Probably...
    month_summary = []
    for e, h in zip(event_sum.all(), helper_sum.all()):
        assert(e['month']==h['month'])
        month_summary.append({**e, **h})

    return ({
        'people_totals': people_totals,
        'event_totals': event_totals,
        'helper_totals': helper_totals,
        'month_summary': month_summary
        })




