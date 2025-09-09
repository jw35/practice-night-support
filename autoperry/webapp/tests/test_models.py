
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

from webapp.models import Event, Volunteer


from datetime import datetime, date, timedelta

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

        cls.live1 = user_model.objects.create_user(
            email='live1@autoperry.com',
            password='password',
            first_name='Denise',
            last_name='Live1',
            tower='Little Shelford',
            email_validated=timezone.now(),
            approved=timezone.now())

        cls.live2 = user_model.objects.create_user(
            email='live2@autoperry.com',
            password='password',
            first_name='Dennis',
            last_name='Live2',
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

        cls.today = date.today()
        cls.testday = date(cls.today.year, 12, 5)

        # This year
        cls.event3 = Event.objects.create(
            start=datetime(cls.today.year, 12, 5, hour=14, minute=0),
            end=datetime(cls.today.year, 12, 5, hour=15, minute=0),
            location='Whittlesford',
            helpers_required=2,
            owner=cls.owner,
            contact_address=None,
            notes='Ab C#',
            alerts=True)



    def test_event_contact(self):

        self.assertEqual(self.event.contact, 'owner@autoperry.com')

        self.event.contact_address = 'contact@ringing_events.org'
        self.assertEqual(self.event.contact, 'contact@ringing_events.org')



    def test_event_when(self):

        self.assertEqual(self.event.when, 'Saturday, 5 March 1960, 2:00 to 3:00 p.m.')
        self.assertEqual(self.event.short_when, 'Sat, 5 Mar 1960, 2:00-3:00')

        self.assertEqual(self.event2.when, 'Saturday, 5 March 1960, 11:00 a.m. to 1:00 p.m.')
        self.assertEqual(self.event2.short_when, 'Sat, 5 Mar 1960, 11:00 a.m.-1:00 p.m.')

        self.assertEqual(self.event3.when, f'{self.testday.strftime("%A")}, 5 December {self.testday.year}, 2:00 to 3:00 p.m.')
        self.assertEqual(self.event3.short_when, f'{self.testday.strftime("%a")}, 5 Dec, 2:00-3:00')



    def test_event_get_absolute_url(self):

        self.assertEqual(self.event.get_absolute_url(), '/event/1/')


    def test_event_helpers_needed(self):

        # Move event into the future
        self.event.start = timezone.now()+timedelta(days=1)

        # Want 2, have none
        self.assertTrue(self.event.helpers_needed)

        # Add two volunteers
        self.event.helpers.add(self.live1)
        self.event.helpers.add(self.live2)

        self.assertFalse(self.event.helpers_needed)

        # Withdraw one
        volunteer1 = Volunteer.objects.get(event=self.event, person=self.live1)
        volunteer1.withdrawn = timezone.now()
        volunteer1.save()

        self.assertTrue(self.event.helpers_needed)


    def test_event_current_helpers(self):

        self.assertFalse(self.event.has_current_helper(self.live1))
        self.assertFalse(self.event.has_current_helper(self.live2))

        self.assertEqual(len(self.event.current_helpers),0)

        # Add two volunteers to event
        self.event.helpers.add(self.live1)
        self.event.helpers.add(self.live2)

        self.assertTrue(self.event.has_current_helper(self.live1))
        self.assertTrue(self.event.has_current_helper(self.live2))

        self.assertEqual(len(self.event.current_helpers),2)
        self.assertIn(self.live1, self.event.current_helpers)
        self.assertIn(self.live2, self.event.current_helpers)

        # Withdraw one
        volunteer1 = Volunteer.objects.get(event=self.event, person=self.live1)
        volunteer1.withdrawn = timezone.now()
        volunteer1.save()

        self.assertFalse(self.event.has_current_helper(self.live1))
        self.assertTrue(self.event.has_current_helper(self.live2))

        self.assertEqual(len(self.event.current_helpers),1)
        self.assertNotIn(self.live1, self.event.current_helpers)
        self.assertIn(self.live2, self.event.current_helpers)

        volunteer2 = Volunteer.objects.get(event=self.event, person=self.live2)
        volunteer2.declined = timezone.now()
        volunteer2.save()

        self.assertFalse(self.event.has_current_helper(self.live1))
        self.assertFalse(self.event.has_current_helper(self.live2))

        self.assertEqual(len(self.event.current_helpers),0)
        self.assertNotIn(self.live1, self.event.current_helpers)
        self.assertNotIn(self.live2, self.event.current_helpers)


    def test_past(self):

        self.assertTrue(self.event.past)

        # Move event into the future
        self.event.start = timezone.now()+timedelta(days=1)

        self.assertFalse(self.event.past)





    def test_volunteer_managers(self):

        # No volunteers
        self.assertEqual(len(self.event.volunteer_set.all()), 0)
        self.assertEqual(len(self.event.volunteer_set.current()), 0)

        self.event.helpers.add(self.live1)
        self.event.helpers.add(self.live2)

        # Add a couple of volunteers
        volunteer1 = Volunteer.objects.get(event=self.event, person=self.live1)
        volunteer2 = Volunteer.objects.get(event=self.event, person=self.live2)

        self.assertEqual(str(volunteer1), '"Denise Live1 [#2]"/"Little Shelford - Sat, 5 Mar 1960, 2:00-3:00 [#1]" [#1]')

        self.assertTrue(volunteer1.current)
        self.assertTrue(volunteer2.current)

        self.assertEqual(len(self.event.volunteer_set.all()), 2)
        self.assertEqual(len(self.event.volunteer_set.current()), 2)

        # One of them withdraws
        volunteer1.withdrawn = timezone.now()
        volunteer1.save()

        self.assertFalse(volunteer1.current)
        self.assertTrue(volunteer2.current)

        self.assertEqual(len(self.event.volunteer_set.all()), 2)
        self.assertEqual(len(self.event.volunteer_set.current()), 1)

        # And the other is declined
        volunteer2.declined = timezone.now()
        volunteer2.save()

        self.assertFalse(volunteer1.current)
        self.assertFalse(volunteer2.current)

        self.assertEqual(len(self.event.volunteer_set.all()), 2)
        self.assertEqual(len(self.event.volunteer_set.current()), 0)

