from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from django.template.loader import render_to_string
from django.core.mail import send_mail

import datetime

from webapp.models import Event
from custom_user.models import User

class Command(BaseCommand):
    help = 'Send email reminders to event helpers'

    def add_arguments(self, parser):

        parser.add_argument(
            '--really',
            action='store_true',
            help='Actually send mail and update the database',
        )

        parser.add_argument(
            '--thisweek',
            action='store_true',
            help='Process reminders for the current week, rather than the next one',
        )

    def handle(self, *args, **options):

        # Remind all owners with send_email 'yes' of all non-cancelled events that
        # start from now and before midnight the day after tomorrow and which haven't
        # already triggered reminders.

        now = timezone.now()

        last_monday = now.replace(hour=0, minute=0, second=0, microsecond=0) - datetime.timedelta(days=now.weekday())
        self.stdout.write(self.style.NOTICE(f'Last Monday {last_monday}'))

        if options['thisweek']:
            start = now
            cutoff = last_monday + datetime.timedelta(days=7)
        else:
            start = last_monday + datetime.timedelta(days=7)
            cutoff = last_monday + datetime.timedelta(days=14)

        last_day = cutoff - datetime.timedelta(1)

        self.stdout.write(self.style.NOTICE(f'Date range is is {start} .. {cutoff}'))

        users = (User.objects.all()
            .filter(is_active=True)
            .filter(send_notifications=True))

        for user in users:

            events = (Event.objects.all()
                .filter(helpers=user)
                .filter(cancelled=None)
                .filter(start__gt=start)
                .filter(start__lt=cutoff))

            if events:

                if options['really']:
                    message = render_to_string("helper_reminder_email_message.html",
                        { "events": events, 'start': start,'last_day': last_day, 'this_week': options['thisweek'] })
                    subject = render_to_string("helper_reminder_email_subject.html",
                        { "events": events, 'start': start,'last_day': last_day, 'this_week': options['thisweek'] })
                    success = user.email_user(subject, message)
                    if success:
                        self.stdout.write(self.style.SUCCESS(f'Reminded {user} about {len(events)} events from {start} to {cutoff}'))
                    else:
                        self.stdout.write(self.style.ERROR(f'Failed to remind {user} about {len(events)} events from {start} to {cutoff}'))

                    user.reminded_upto = cutoff
                    user.save()

                else:
                    self.stdout.write(self.style.NOTICE(f'Need to reminded {user} about {len(events)} events from {start} to {cutoff}'))
