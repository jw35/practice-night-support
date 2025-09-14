from django.conf import settings
from django.core.mail import EmailMessage
from django.core.management.base import BaseCommand
from django.db.models import Count, F, Q
from django.template.loader import render_to_string
from django.utils import timezone
from django.core.mail import send_mail

import datetime

from webapp.models import Event
from custom_user.models import User

class Command(BaseCommand):
    help = 'Send an advert about upcoming events'

    def add_arguments(self, parser):

        parser.add_argument(
            '--really',
            action='store_true',
            help='Actually send mail',
        )

        parser.add_argument(
            '--weeks',
            type=int,
            default=2,
            help='Number of weeks to look ahead',
        )

    def handle(self, *args, **options):

        # Remind all owners with send_email 'yes' of all non-cancelled events that
        # start from now and before midnight the day after tomorrow and which haven't
        # already triggered reminders.

        now = timezone.now()
        cutoff = now + datetime.timedelta(weeks=options['weeks'])

        self.stdout.write(self.style.NOTICE(f'Date range is is {now} .. {cutoff}'))

        events = (Event.objects.all()
                  .filter(start__gte=now)
                  .filter(start__lte=cutoff)
                  .filter(cancelled=None)
                  .annotate(helpers_available=Count('volunteer', filter=(Q(volunteer__withdrawn=None) & Q(volunteer__declined=None))))
                  .filter(helpers_required__gt=F("helpers_available"))
                  .order_by('start', 'location'))

        if not events:
            self.stdout.write(self.style.NOTICE('No events in selected range'))

        users = (User.objects.all()
            .filter(send_other=True)
            .filter(cancelled=None)
            .filter(suspended=None)
            .filter(email_blocked=None)
            .exclude(email_validated=None)
            .exclude(approved=None))

        if not users:
            self.stdout.write(self.style.NOTICE('No users eligible for this email'))

        to_addresses = users.values_list('email', flat=True)

        if events and users:

            if options['really']:

                template = 'email-advert'
                context = { 'weeks': options['weeks'],
                            'events': events ,
                            'domain': settings.WEBAPP_DOMAIN,
                            'scheme': settings.WEBAPP_SCHEME
                           }
                message = render_to_string(f"webapp/email/{template}-message.txt", context).strip()
                subject = render_to_string(f"webapp/email/{template}-subject.txt", context).strip()

                EmailMessage(subject=subject,
                    body=message,
                    bcc=to_addresses,
                    cc=(settings.DEFAULT_FROM_EMAIL,)).send()

                self.stdout.write(self.style.NOTICE(f'Advertised { len(events) } events to { len(to_addresses) } addresses: {", ".join(to_addresses)}'))

            else:
                self.stdout.write(self.style.NOTICE(f'Need to advertise { len(events) } events to { len(to_addresses) } addresses: {", ".join(to_addresses)}'))
