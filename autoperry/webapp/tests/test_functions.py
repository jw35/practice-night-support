
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from django.core import mail
from django.test import TestCase
from django.utils import timezone

from webapp.models import Event

from datetime import timedelta
import re

from webapp.util import send_template_email

class FunctionTestCase(TestCase):

    @classmethod
    def setUpTestData(cls):

        user_model = get_user_model()

        cls.registered = user_model.objects.create_user(
            email='registered@autoperry.com',
            password='password',
            first_name='Albert',
            last_name='Registered',
            tower='Little Shelford')

        cls.validated = user_model.objects.create_user(
            email='validated@autoperry.com',
            password='password',
            first_name='Betty',
            last_name='Validated',
            tower='Little Shelford',
            email_validated=timezone.now())

        # Note: approved, but email not yet validated
        cls.approved = user_model.objects.create_user(
            email='approved@autoperry.com',
            password='password',
            first_name='Charles',
            last_name='Approved',
            tower='Little Shelford',
            approved=timezone.now())

        cls.live = user_model.objects.create_user(
            email='live@autoperry.com',
            password='password',
            first_name='Denise',
            last_name='Live',
            tower='Little Shelford',
            email_validated=timezone.now(),
            approved=timezone.now())

        cls.suspended = user_model.objects.create_user(
            email='suspended@autoperry.com',
            password='password',
            first_name='Egbert',
            last_name='Suspended',
            tower='Little Shelford',
            email_validated=timezone.now(),
            approved=timezone.now(),
            suspended=timezone.now())

        cls.blocked = user_model.objects.create_user(
            email='blocked@autoperry.com',
            password='password',
            first_name='Francis',
            last_name='Blocked',
            tower='Little Shelford',
            email_validated=timezone.now(),
            approved=timezone.now(),
            email_blocked=timezone.now())

        cls.admin_group = Group.objects.create(name='webapp.administrators')
        permission = Permission.objects.get(codename='administrator')
        cls.admin_group.permissions.add (permission)
        cls.admin = user_model.objects.create_user(
            email='Admin@autoperry.com',
            password='password',
            first_name='Fiona',
            last_name='Administrator',
            tower='Little Shelford',
            email_validated=timezone.now(),
            approved=timezone.now())
        cls.admin.groups.add(cls.admin_group)

        cls.owner = user_model.objects.create_user(
            email='owner@autoperry.com',
            password='password',
            first_name='Geoff',
            last_name='Owner',
            tower='Little Shelford',
            email_validated=timezone.now(),
            approved=timezone.now())

        cls.cancelled = user_model.objects.create_user(
            email='anonymous',
            password='',
            first_name='Harriet',
            last_name='Cancelled',
            tower='',
            email_validated=timezone.now(),
            approved=timezone.now(),
            cancelled=timezone.now())

        cls.future_event = Event.objects.create(
            start=timezone.now() + timedelta(days=1),
            end=timezone.now() + timedelta(days=1, hours=1, minutes=30),
            location='Little Shelford',
            helpers_required=2,
            owner=cls.live,
            contact_address=None,
            notes='Ab C#',
            alerts=True)

    def test_send_template_email(self):

        # Normal live user should get mail
        send_template_email(self.live,'email-email',{},force=False)
        self.assertEqual(len(mail.outbox), 1)
        mail.outbox = []

        # But not if they haven't validated their address
        self.live.email_validated = None
        send_template_email(self.live,'email-email',{},force=False)
        self.assertEqual(len(mail.outbox), 0)
        mail.outbox = []

        # ... or have elected not to have mail
        self.live.email_validated = timezone.now()
        self.live.send_notifications = False
        send_template_email(self.live,'email-email',{},force=False)
        self.assertEqual(len(mail.outbox), 0)
        mail.outbox = []

        # ... or are cancelled
        send_template_email(self.cancelled,'email-email',{},force=False)
        self.assertEqual(len(mail.outbox), 0)
        mail.outbox = []

        # ... or are suspended
        send_template_email(self.suspended,'email-email',{},force=False)
        self.assertEqual(len(mail.outbox), 0)
        mail.outbox = []

        # ... or are blocked
        send_template_email(self.blocked,'email-email',{},force=False)
        self.assertEqual(len(mail.outbox), 0)
        mail.outbox = []

    def test_send_template_email_force(self):

        send_template_email(self.live,'email-email',{},force=True)
        self.assertEqual(len(mail.outbox), 1)
        mail.outbox = []

        self.live.email_validated = None
        send_template_email(self.live,'email-email',{},force=True)
        self.assertEqual(len(mail.outbox), 1)
        mail.outbox = []

        self.live.email_validated = timezone.now()
        self.live.send_notifications = False
        send_template_email(self.live,'email-email',{},force=True)
        self.assertEqual(len(mail.outbox), 1)
        mail.outbox = []

        # blocked OK (else can't recieeve validatio messages!)
        send_template_email(self.blocked,'email-email',{},force=True)
        self.assertEqual(len(mail.outbox), 1)
        mail.outbox = []

        # Still not sending if suspended
        send_template_email(self.cancelled,'email-email',{},force=True)
        self.assertEqual(len(mail.outbox), 0)
        mail.outbox = []

        # ... or cancelled
        send_template_email(self.suspended,'email-email',{},force=True)
        self.assertEqual(len(mail.outbox), 0)
        mail.outbox = []