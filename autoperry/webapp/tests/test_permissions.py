
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from django.core import mail
from django.test import TestCase
from django.utils import timezone

from webapp.models import Event

from datetime import timedelta

index_url = '/'

public_urls = ['/privacy',
               '/help/about',
               '/help/organisers',
               '/help/helpers',
               '/account/create',
               #'/account/confirm/XXX/XXX',
               '/accounts/password_reset/',
               '/accounts/password_reset/done/',
               '/accounts/reset/XXX/XXX/',
               '/accounts/reset/done/',
              ]

logout_url = '/accounts/logout/'

limbo_urls  = ['/account',
               '/account/resend',
               '/account/edit',
               '/account/cancel',
               '/accounts/password_change/',
               '/accounts/password_change/done/',
               ]

core_urls   = ['/events',
               '/event/create',
               '/event/1/cancel',
               '/event/1/edit',
               '/event/1/clone',
               '/event/1/volunteer',
               '/event/1/unvolunteer',
               '/event/1/decline/1',
               ]

admin_urls  = ['/admin/send-emails',
               '/admin/account-list',
               '/admin/account-approve/1',
               '/admin/account-toggle/suspend/1',
               ]



class DecoratorTestCase(TestCase):

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

        cls.admin

        cls.owner = user_model.objects.create_user(
            email='owner@autoperry.com',
            password='password',
            first_name='Geoff',
            last_name='Owner',
            tower='Little Shelford',
            email_validated=timezone.now(),
            approved=timezone.now())

        cls.future_event = Event.objects.create(
            start=timezone.now() + timedelta(days=1),
            end=timezone.now() + timedelta(days=1, hours=1, minutes=30),
            location='Little Shelford',
            helpers_required=2,
            owner=cls.live,
            contact_address=None,
            notes='Ab C#',
            alerts=True)


    def test_anonymous(self):

        response = self.client.get(index_url)
        self.assertEquals(response.status_code, 200, '/')
        self.assertContains(response, 'Please sign in', msg_prefix='/')

        for url in public_urls:
            response = self.client.get(url)
            self.assertEquals(response.status_code, 200, url)

        for url in limbo_urls + core_urls + admin_urls:
            response = self.client.get(url)
            self.assertRedirects(response, '/?next=' + url, msg_prefix=url)

        response = self.client.get(logout_url)
        self.assertRedirects(response, '/', msg_prefix=logout_url)


    def test_limbo(self):

        for user in (self.registered, self.validated, self.approved, self.suspended):

            self.assertTrue(self.client.login(username=user.email, password='password'),f'Logging in {user.email}')

            response = self.client.get(index_url)
            self.assertEquals(response.status_code, 200, '/')
            if not user.approved:
                self.assertContains(response, 'approved by an administrator', msg_prefix='/')
            if not user.email_validated:
                self.assertContains(response, 'confirm your email address', msg_prefix='/')
            if user.suspended:
                self.assertContains(response, 'has been <b>suspended</b>', msg_prefix='/')

            for url in public_urls + limbo_urls:
                response = self.client.get(url)
                self.assertEquals(response.status_code, 200, url)

            for url in core_urls + admin_urls:
                response = self.client.get(url)
                self.assertRedirects(response, '/?next=' + url, msg_prefix=url)

            response = self.client.get(logout_url)
            self.assertRedirects(response, '/', msg_prefix=logout_url)


    def test_live(self):

        user = self.live
        self.assertTrue(self.client.login(username=user.email, password='password'),f'Logging in {user.email}')

        response = self.client.get(index_url)
        self.assertEquals(response.status_code, 200, '/')
        # Deliberately 'vents' to cope with 'Events needing helpers' and 'No events needing helpers''
        self.assertContains(response, 'vents needing helpers', msg_prefix='/')

        for url in public_urls + limbo_urls + core_urls:
                response = self.client.get(url)
                # CAncel and Unvolunteer redirect because not allowed by this user
                if url == '/account/cancel' or url == '/event/1/unvolunteer':
                    self.assertEquals(response.status_code, 302, url)
                else:
                    self.assertEquals(response.status_code, 200, url)

        for url in admin_urls:
            response = self.client.get(url)
            self.assertEquals(response.status_code, 403, url)

        response = self.client.get(logout_url)
        self.assertRedirects(response, '/', msg_prefix=logout_url)


    def test_admin(self):

        user = self.admin
        self.assertTrue(self.client.login(username=user.email, password='password'),f'Logging in {user.email}')

        response = self.client.get(index_url)
        self.assertEquals(response.status_code, 200, '/')
        # Deliberately 'vents' to cope with 'Events needing helpers' and 'No events needing helpers''
        self.assertContains(response, 'vents needing helpers', msg_prefix='/')

        for url in public_urls + limbo_urls + core_urls + admin_urls:
                response = self.client.get(url)
                # cancel redirect because not allowed by this user
                if url == '/event/1/cancel' or url == '/event/1/edit' or url == '/event/1/decline/1' or url == '/event/1/unvolunteer':
                    self.assertEquals(response.status_code, 302, url)
                else:
                    self.assertEquals(response.status_code, 200, url)

        response = self.client.get(logout_url)
        self.assertRedirects(response, '/', msg_prefix=logout_url)

