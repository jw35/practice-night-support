from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from django.core.mail import send_mail

import datetime

from webapp.models import Event
from webapp.util import send_template_email

class Command(BaseCommand):
    help = 'Send email reminders to event owners'

    def add_arguments(self, parser):

        parser.add_argument(
            '--really',
            action='store_true',
            help='Actually send mail and update the database',
        )

    def handle(self, *args, **options):

        # Remind all owners with send_email 'yes' of all non-cancelled events that
        # start from now and before midnight the day after tomorrow and which haven't
        # already triggered reminders.

        now = timezone.now()

        cutoff = now.replace(hour=0, minute=0, second=0, microsecond=0) + datetime.timedelta(days=3)

        self.stdout.write(self.style.NOTICE(f'Cutoff date is {cutoff}'))

        events = (Event.objects.all()
            .filter(owner__send_notifications=True)
            .filter(cancelled=None)
            .filter(start__gt=timezone.now())
            .filter(start__lte=cutoff)
            .filter(owner_reminded=None))

        for event in events:

            if options['really']:
                send_template_email(event.owner, "event-reminder", { "event": event })

                event.owner_reminded = now
                event.save()

            else:
                self.stdout.write(self.style.NOTICE(f'Need to remind {event.owner} about {event}'))