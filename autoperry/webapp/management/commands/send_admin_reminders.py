from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from django.core.mail import send_mail

import datetime

from webapp.models import Event
from webapp.util import send_template_email

class Command(BaseCommand):
    help = 'Send email reminders to administrators'

    def add_arguments(self, parser):

        parser.add_argument(
            '--really',
            action='store_true',
            help='Actually send mail',
        )

    def handle(self, *args, **options):

        # Remind administrators of any pending account approvals

        now = timezone.now()

        # Anyone awaiting approval who hasn't been cancelled or suspended
        # and has been waiting more than 24 hours
        users = (get_user_model().objects.all()
            .filter(approved=None)
            .filter(cancelled=None)
            .filter(suspeded=None)
            .filter(date_joined__lte=now-datetime.timedelta(hours=24))
            .order_by('date_joined'))

        if users:

            if options['really']:
                send_template_email(settings.DEFAULT_FROM_EMAIL, "account-approval-reminder", { "users": users })
            else:
                self.stdout.write(self.style.NOTICE(f'Approval needed for {len(users)} accounts'))