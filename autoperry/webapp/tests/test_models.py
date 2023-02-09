
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

from webapp.models import Event


from datetime import datetime

class FunctionTestCase(TestCase):

    @classmethod
    def setUpTestData(cls):

        user_model = get_user_model()

        cls.owner = user_model.objects.create_user(
            email='owner@autoperry.com',
            password='password',
            first_name='Geoff',
            last_name='Owner',
            tower='Little Shelford',
            email_validated=timezone.now(),
            approved=timezone.now())

        # Starts and ends in the afternoon
        cls.event = Event.objects.create(
            start=datetime(1960, 3, 5, hour=14, minute=0),
            end=datetime(1960, 3, 5, hour=15, minute=0),
            location='Little Shelford',
            helpers_required=2,
            owner=cls.owner,
            contact_address=None,
            notes='Ab C#',
            alerts=True)

        # Starts in the morning, ends i the afternoon
        cls.event2 = Event.objects.create(
            start=datetime(1960, 3, 5, hour=11, minute=0),
            end=datetime(1960, 3, 5, hour=13, minute=0),
            location='Whittlesford',
            helpers_required=2,
            owner=cls.owner,
            contact_address=None,
            notes='Ab C#',
            alerts=True)

        # In December
        cls.event3 = Event.objects.create(
            start=datetime(1960, 12, 5, hour=14, minute=0),
            end=datetime(1960, 12, 5, hour=15, minute=0),
            location='Whittlesford',
            helpers_required=2,
            owner=cls.owner,
            contact_address=None,
            notes='Ab C#',
            alerts=True)

    def test_contact(self):

        self.assertEqual(self.event.contact, 'owner@autoperry.com')

        self.event.contact_address = 'contact@ringing_events.org'
        self.assertEqual(self.event.contact, 'contact@ringing_events.org')

    def test_when(self):

        self.assertEqual(self.event.when, 'Saturday, 5 March 1960, 2:00 to 3:00 p.m.')
        self.assertEqual(self.event.short_when, 'Sat, 5 Mar, 2:00-3:00')

        self.assertEqual(self.event2.when, 'Saturday, 5 March 1960, 11:00 a.m. to 1:00 p.m.')
        self.assertEqual(self.event2.short_when, 'Sat, 5 Mar, 11:00 a.m.-1:00 p.m.')

        self.assertEqual(self.event3.when, 'Monday, 5 December 1960, 2:00 to 3:00 p.m.')
        self.assertEqual(self.event3.short_when, 'Mon, 5 Dec 1960, 2:00-3:00')

    def test_get_absolute_url(self):

        self.assertEqual(self.event.get_absolute_url(), '/event/1/')

