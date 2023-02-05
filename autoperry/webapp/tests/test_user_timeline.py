
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from django.core import mail
from django.test import TestCase
from django.utils import timezone

from webapp.models import Event

from datetime import timedelta
import re



class TemplateTestCase(TestCase):

    @classmethod
    def setUpTestData(cls):

        user_model = get_user_model()

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


    def test_lifecycle(self):

        user_model = get_user_model()

        #
        # Fill in the registration form
        #

        response = self.client.post('/account/create',
            { 'email': 'nweuser@new.com',
              'first_name': 'New',
              'last_name': 'User',
              'tower': 'Newton',
              'send_notifications': 'Yes',
              'send_other': 'Yes',
              'password1': 'passwordABCDE123450987',
              'password2': 'passwordABCDE123450987'
            })

        self.assertEquals(response.status_code, 200, 'Created user')
        self.assertTemplateUsed(response, 'webapp/account-create-pending.html')

        user = user_model.objects.get(email='nweuser@new.com')
        self.assertFalse(user.email_validated, 'email validation flag unset')
        self.assertFalse(user.approved, 'approved flag unset')

        #
        # Check emails sent
        #

        self.assertEquals(len(mail.outbox), 2)

        self.assertEquals(mail.outbox[0].subject, '[AutoPerry]: Please confirm your email address')
        self.assertEquals(mail.outbox[0].from_email, settings.DEFAULT_FROM_EMAIL)
        self.assertEquals(mail.outbox[0].to[0], 'nweuser@new.com')
        body = mail.outbox[0].body

        pattern = r'/account/confirm/(?P<uid>[^/]+)/(?P<token>.*)$'
        match = re.search(pattern, body, re.MULTILINE)
        self.assertNotEqual(match, None, 'match worked')
        uid = match.group('uid')
        token = match.group('token')

        self.assertEquals(mail.outbox[1].subject, '[AutoPerry]: New account created - New User')
        self.assertEquals(mail.outbox[1].from_email, settings.DEFAULT_FROM_EMAIL)
        self.assertEquals(mail.outbox[1].to[0], settings.DEFAULT_FROM_EMAIL)

        mail.outbox = []

        #
        # Respond to email validation
        #

        response = self.client.get(f'/account/confirm/{uid}/{token}', follow=True)
        self.assertContains(response, 'Your email address has been confirmed', status_code=200, msg_prefix='validation confirmation message')

        user.refresh_from_db()
        self.assertTrue(user.email_validated, 'email validation flag set')
        self.assertFalse(user.approved, 'approved flag still unset')

        # Doesn't send any email
        self.assertEquals(len(mail.outbox), 0)

        #
        # Become an administrator
        #

        self.assertTrue(self.client.login(username=self.admin.email, password='password'),f'Logging in {self.admin.email}')

        response = self.client.get('/admin/account-approve-list')
        self.assertEquals(response.status_code, 200, 'getting approval list')

        pattern = r'href="/admin/account-approve/(?P<uid>.*?)"'
        match = re.search(pattern, response.content.decode('utf-8'), re.MULTILINE)
        self.assertNotEqual(match, None, 'match worked')
        uid = match.group('uid')

        response = self.client.get(f'/admin/account-approve/{uid}')
        self.assertContains(response, 'nweuser@new.com')

        response = self.client.post(f'/admin/account-approve/{uid}',
            { 'confirm': 'Approve'})
        self.assertRedirects(response, '/admin/account-approve-list')

        user.refresh_from_db()
        self.assertTrue(user.email_validated, 'email validation flag still set')
        self.assertTrue(user.approved, 'approved flag set')

        #
        # Check email sent
        #

        self.assertEquals(len(mail.outbox), 1)
        self.assertEquals(mail.outbox[0].subject, '[AutoPerry]: Your account has been approved')
        self.assertEquals(mail.outbox[0].from_email, settings.DEFAULT_FROM_EMAIL)
        self.assertEquals(mail.outbox[0].to[0], 'nweuser@new.com')

        mail.outbox = []

        #
        # Suspend the user - still an administrator
        #

        self.assertFalse(user.suspended, 'not yet suspended')
        response = self.client.post(f'/admin/account-toggle/suspend/{uid}',
            { 'confirm': 'Suspend'})
        self.assertRedirects(response, '/admin/account-list')
        user.refresh_from_db()
        self.assertTrue(user.suspended, 'now suspended')

        #
        # Put them back
        #

        response = self.client.post(f'/admin/account-toggle/enable/{uid}',
            { 'confirm': 'Enable'})
        self.assertRedirects(response, '/admin/account-list')
        user.refresh_from_db()
        self.assertFalse(user.suspended, 'reenabled')

        #
        # And finally cancel
        #

        # Switch to the user
        self.client.logout()
        self.assertTrue(self.client.login(username=user.email, password='passwordABCDE123450987'),f'Logging in {user.email}')

        response = self.client.post('/account/cancel',
            { 'confirm': 'Yes, cancel my account'})
        self.assertRedirects(response, '/')

        user.refresh_from_db()
        self.assertTrue(user.cancelled, 'cacelled')
        self.assertEqual(user.first_name, '')
