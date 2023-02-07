from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from django.core import mail
from django.test import TestCase
from django.utils import timezone

from webapp.models import Event

from datetime import timedelta



class PermissionsTestCase(TestCase):

    @classmethod
    def setUpTestData(cls):

        user_model = get_user_model()

        cls.live = user_model.objects.create_user(
            email='live@autoperry.com',
            password='password',
            first_name='Denise',
            last_name='Live',
            tower='Little Shelford',
            email_validated=timezone.now(),
            approved=timezone.now(),
            send_other=False)

        cls.admin_group = Group.objects.create(name='webapp.administrators')
        permission = Permission.objects.get(codename='administrator')
        cls.admin_group.permissions.add (permission)
        cls.admin = user_model.objects.create_user(
            email='admin@autoperry.com',
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

        cls.future_event = Event.objects.create(
            start=timezone.now() + timedelta(days=1),
            end=timezone.now() + timedelta(days=1, hours=1, minutes=30),
            location='Little Shelford',
            helpers_required=2,
            owner=cls.owner,
            contact_address=None,
            notes='Ab C#',
            alerts=True)

        cls.past_event = Event.objects.create(
            start=timezone.now() + timedelta(days=-1),
            end=timezone.now() + timedelta(days=-1, hours=1, minutes=30),
            location='Little Shelford',
            helpers_required=2,
            owner=cls.owner,
            contact_address=None,
            notes='Ab C#',
            alerts=True)

        cls.cancelled = Event.objects.create(
            start=timezone.now() + timedelta(days=1),
            end=timezone.now() + timedelta(days=1, hours=1, minutes=30),
            location='Little Shelford',
            helpers_required=2,
            owner=cls.owner,
            contact_address=None,
            notes='Ab C#',
            alerts=True,
            cancelled=timezone.now())

        cls.future_event.helpers.add(cls.live)

    def test_failing_login(self):

        response = self.client.post('/',
            { 'username': 'nonsuch@autoperry.com',
              'password': 'password',
            })

        self.assertEquals(response.status_code, 200)
        self.assertTemplateUsed(response, 'webapp/index.html')
        self.assertContains(response, 'Bad email address or password')



    def test_successfull_login(self):

        response = self.client.post('/',
            { 'username': 'live@autoperry.com',
              'password': 'password',
            }, follow=True)

        self.assertEquals(response.status_code, 200)
        self.assertTemplateUsed(response, 'webapp/index.html')
        self.assertContains(response, 'vents needing helpers')


    def test_event_create(self):

        self.assertTrue(self.client.login(username=self.owner.email, password='password'),f'Logging in {self.owner.email}')

        anchor = timezone.now()+timedelta(days=1)

        response = self.client.post('/event/create/',
            { 'date': anchor.date(),
              'start_time': anchor.time(),
              'end_time': (anchor+timedelta(hours=2)).time(),
              'location': 'Whittlesford',
              'helpers_required': 2,
              'contact_address': '',
              'notes': 'D#',
              'alerts': 'yes',
            }, follow=True)

        self.assertEquals(response.status_code, 200)
        self.assertTemplateUsed(response, 'webapp/event.html')
        self.assertContains(response, 'Event successfully created')


    def test_event_edit(self):

        self.assertTrue(self.client.login(username=self.owner.email, password='password'),f'Logging in {self.owner.email}')

        anchor = timezone.now()+timedelta(days=1)

        response = self.client.post('/event/1/edit/',
            { 'date': anchor.date(),
              'start_time': anchor.time(),
              'end_time': (anchor+timedelta(hours=2)).time(),
              'location': 'Whittlesford',
              'helpers_required': 2,
              'contact_address': '',
              'notes': 'D#',
              'alerts': 'yes',
            }, follow=True)

        self.assertEquals(response.status_code, 200)
        self.assertTemplateUsed(response, 'webapp/event.html')
        self.assertContains(response, 'Event successfully updated')

        self.assertEquals(len(mail.outbox), 1)

        self.assertEquals(mail.outbox[0].subject, '[AutoPerry]: Help request ALTERED')
        self.assertEquals(mail.outbox[0].from_email, settings.DEFAULT_FROM_EMAIL)
        self.assertEquals(mail.outbox[0].to[0], 'live@autoperry.com')


    def test_past_event_edit(self):

        self.assertTrue(self.client.login(username=self.owner.email, password='password'),f'Logging in {self.owner.email}')

        response = self.client.get('/event/2/edit/', follow=True)

        self.assertEquals(response.status_code, 200)
        self.assertTemplateUsed(response, 'webapp/event.html')
        self.assertContains(response, 'This event has already happened ')


    def test_cancelled_event_edit(self):

        self.assertTrue(self.client.login(username=self.owner.email, password='password'),f'Logging in {self.owner.email}')

        response = self.client.get('/event/3/edit/', follow=True)

        self.assertEquals(response.status_code, 200)
        self.assertTemplateUsed(response, 'webapp/event.html')
        self.assertContains(response, 'The request for help at this event has been cancelled')


    def test_event_cancel(self):

        self.assertTrue(self.client.login(username=self.owner.email, password='password'),f'Logging in {self.owner.email}')

        response = self.client.post('/event/1/cancel/',
            { 'confirm': 'Cancel',
            }, follow=True)

        self.assertEquals(response.status_code, 200)
        self.assertTemplateUsed(response, 'webapp/event.html')
        self.assertContains(response, 'Event cancelled')

        self.assertEquals(len(mail.outbox), 1)

        self.assertEquals(mail.outbox[0].subject, f'[AutoPerry]: Help request CANCELLED - {self.future_event.location}, {self.future_event.short_when}')
        self.assertEquals(mail.outbox[0].from_email, settings.DEFAULT_FROM_EMAIL)
        self.assertEquals(mail.outbox[0].to[0], 'live@autoperry.com')


    def test_past_event_cancel(self):

        self.assertTrue(self.client.login(username=self.owner.email, password='password'),f'Logging in {self.owner.email}')

        response = self.client.get('/event/2/cancel/', follow=True)

        self.assertEquals(response.status_code, 200)
        self.assertTemplateUsed(response, 'webapp/event.html')
        self.assertContains(response, 'This event has already happened ')


    def test_cancelled_event_cancel(self):

        self.assertTrue(self.client.login(username=self.owner.email, password='password'),f'Logging in {self.owner.email}')

        response = self.client.get('/event/3/cancel/', follow=True)

        self.assertEquals(response.status_code, 200)
        self.assertTemplateUsed(response, 'webapp/event.html')
        self.assertContains(response, 'The request for help at this event has already been cancelled')



    def test_volunteer(self):

        self.assertTrue(self.client.login(username=self.owner.email, password='password'),f'Logging in {self.owner.email}')

        response = self.client.post('/event/1/volunteer/',
            { 'confirm': 'Volunteer',
            }, follow=True)

        self.assertEquals(response.status_code, 200)
        self.assertTemplateUsed(response, 'webapp/event.html')
        self.assertContains(response, 'You have been added as a helper for this event')

        self.assertEquals(len(mail.outbox), 1)

        self.assertEquals(mail.outbox[0].subject, f'[AutoPerry]: New helper for {self.future_event.location}, {self.future_event.short_when}')
        self.assertEquals(mail.outbox[0].from_email, settings.DEFAULT_FROM_EMAIL)
        self.assertEquals(mail.outbox[0].to[0], 'owner@autoperry.com')

    def test_unvolunteer(self):

        self.assertTrue(self.client.login(username=self.live.email, password='password'),f'Logging in {self.live.email}')

        response = self.client.post('/event/1/unvolunteer/',
            { 'confirm': 'Volunteer',
            }, follow=True)

        self.assertEquals(response.status_code, 200)
        self.assertTemplateUsed(response, 'webapp/event.html')
        self.assertContains(response, 'You are no longer a helper for this event')

        self.assertEquals(len(mail.outbox), 1)

        self.assertEquals(mail.outbox[0].subject, f'[AutoPerry]: Withdrawn helper for {self.future_event.location}, {self.future_event.short_when}')
        self.assertEquals(mail.outbox[0].from_email, settings.DEFAULT_FROM_EMAIL)
        self.assertEquals(mail.outbox[0].to[0], 'owner@autoperry.com')


    def test_decline(self):

        self.assertTrue(self.client.login(username=self.owner.email, password='password'),f'Logging in {self.owner.email}')

        response = self.client.post('/event/1/decline/1/',
            { 'confirm': 'Decline offer',
            }, follow=True)

        self.assertEquals(response.status_code, 200)
        self.assertTemplateUsed(response, 'webapp/event.html')
        self.assertContains(response, f'{self.live} as been removed as a helper')

        self.assertEquals(len(mail.outbox), 1)

        self.assertEquals(mail.outbox[0].subject, f'[AutoPerry]: Help request DECLINED - {self.future_event.location}, {self.future_event.short_when}')
        self.assertEquals(mail.outbox[0].from_email, settings.DEFAULT_FROM_EMAIL)
        self.assertEquals(mail.outbox[0].to[0], 'live@autoperry.com')


    def test_account_edit(self):

        self.assertTrue(self.client.login(username=self.owner.email, password='password'),f'Logging in {self.owner.email}')

        response = self.client.post('/account/edit/',
           {'email': 'megga-owner@autoperry.org.uk',
            'first_name': 'Geffory',
            'last_name': 'Owner-Smith',
            'tower': 'Ros-on-Why',
            'send_notifications': self.owner.send_notifications,
            'send_other': self.owner.send_other,
            }, follow=True)

        self.assertEquals(response.status_code, 200)
        self.assertTemplateUsed(response, 'webapp/account-create-resend.html')
        self.assertContains(response, 'Your account details have been successfully updated')

        # Changed email address, soneeds validating
        self.assertEquals(len(mail.outbox), 1)

        self.assertEquals(mail.outbox[0].subject, '[AutoPerry]: Please confirm your email address')
        self.assertEquals(mail.outbox[0].from_email, settings.DEFAULT_FROM_EMAIL)
        self.assertEquals(mail.outbox[0].to[0], 'megga-owner@autoperry.org.uk')

        self.owner.refresh_from_db()
        self.assertIsNone(self.owner.email_validated)

    def test_send_email(self):

        self.assertTrue(self.client.login(username=self.admin.email, password='password'),f'Logging in {self.admin.email}')

        response = self.client.post('/admin/send-emails/',
           {'helpers': 'yes',
            'organisers': 'yes',
            'rest': 'yes',
            'subject': 'Here we go again',
            'message': 'From the Swedish Prime Minister',
            }, follow=True)

        self.assertEquals(response.status_code, 200)
        self.assertTemplateUsed(response, 'webapp/send-email.html')
        self.assertContains(response, 'Bulk email sent to 2 addresses')

        # Changed email address, soneeds validating
        self.assertEquals(len(mail.outbox), 1)

        self.assertEquals(mail.outbox[0].subject, '[AutoPerry]: Here we go again')
        self.assertEquals(mail.outbox[0].from_email, settings.DEFAULT_FROM_EMAIL)
        self.assertEquals(mail.outbox[0].to, [])
        self.assertEquals(mail.outbox[0].cc, [settings.DEFAULT_FROM_EMAIL])
        self.assertEquals(mail.outbox[0].bcc, ['admin@autoperry.com', 'owner@autoperry.com'])



