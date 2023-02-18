
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from django.core import mail
from django.test import TestCase
from django.utils import timezone

from webapp.models import Event
from webapp.util import build_stats_screen

from datetime import datetime, timedelta





class PermissionsTestCase(TestCase):

    @classmethod
    def setUpTestData(cls):

        user_model = get_user_model()

        # Events from 5/3/1960
        base = datetime(1960, 3, 5, hour=14, minute=0)
        next_month = datetime(1960, 4, 5, hour=14, minute=0)
        # Report being run 1/5/1960
        now = datetime(1960, 5, 1, hour=14, minute=0)
        # So this is in the future 5/5/1960
        future = datetime(1960, 5, 5, hour=14, minute=0)

        one_hour = timedelta(hours=1)
        one_day = timedelta(days=1)
        five_weeks = timedelta(weeks=5)

        # Limbo
        cls.user1 = user_model.objects.create_user(
            email='user1@autoperry.com',
            password='password',
            first_name='Albert',
            last_name='User 1',
            tower='Little Shelford')

        # Live
        cls.user2 = user_model.objects.create_user(
            email='user2@autoperry.com',
            password='password',
            first_name='Betty',
            last_name='User 2',
            tower='Little Shelford',
            email_validated=base,
            approved=base)

        # Live
        cls.user3 = user_model.objects.create_user(
            email='user3@autoperry.com',
            password='password',
            first_name='Charles',
            last_name='User 3',
            tower='Little Shelford',
            email_validated=base,
            approved=base)

        # Cancelled
        cls.user4 = user_model.objects.create_user(
            email='user4@autoperry.com',
            password='password',
            first_name='Denise',
            last_name='User 4',
            tower='Little Shelford',
            email_validated=timezone.now(),
            approved=base,
            cancelled=base)

        cls.event1 = Event.objects.create(
            start=base,
            end=base + one_hour,
            location='Little Shelford',
            helpers_required=2,
            owner=cls.user2)

        cls.event1.helpers.add(cls.user1)
        cls.event1.helpers.add(cls.user2)

        cls.event2 = Event.objects.create(
            start=base + one_day,
            end=base + one_day + one_hour ,
            location='Little Shelford',
            helpers_required=1,
            owner=cls.user3)

        cls.event2.helpers.add(cls.user1)

        cls.event3 = Event.objects.create(
            start=base + (2*one_day),
            end=base + (2*one_day) + one_hour ,
            location='Little Shelford',
            helpers_required=1,
            owner=cls.user2,
            cancelled=next_month)

        cls.event3.helpers.add(cls.user1)

        cls.event4 = Event.objects.create(
            start=next_month,
            end=next_month + one_hour,
            location='Little Shelford',
            helpers_required=1,
            owner=cls.user3)

        cls.event4.helpers.add(cls.user1)

        cls.event5 = Event.objects.create(
            start=future,
            end=future + one_hour,
            location='Little Shelford',
            helpers_required=1,
            owner=cls.user2)

        cls.event5.helpers.add(cls.user1)

        cls.event6 = Event.objects.create(
            start=future + (2*one_hour),
            end=future + (3*one_hour),
            location='Little Shelford',
            helpers_required=1,
            owner=cls.user2,
            cancelled=future+one_day)

        cls.now = now


    def test_overall(self):

        data = build_stats_screen(self.now)

        self.assertEqual(data['people_totals']['total'], 2)
        self.assertEqual(data['people_totals']['pending'], 1)
        self.assertEqual(data['people_totals']['cancelled'], 1)

        self.assertEqual(len(data['month_summary']), 2)

        self.assertEqual(data['month_summary'][0],
            {'month': datetime(1960, 3, 1, 0, 0),
             'events': 2,
             'cancelled_events': 1,
             'owners': 2,
             'locations': 1,
             'helpers_wanted': 3,
             'helpers_provided': 3,
             'distinct_helpers': 2,
             'helpers_cancelled': 1
            })

        self.assertEqual(data['month_summary'][1],
            {'month': datetime(1960, 4, 1, 0, 0),
             'events': 1,
             'cancelled_events': 0,
             'owners': 1,
             'locations': 1,
             'helpers_wanted': 1,
             'helpers_provided': 1,
             'distinct_helpers': 1,
             'helpers_cancelled': 0
            })

        self.assertEqual(data['event_totals'],
            {'events': 3,
             'cancelled_events': 1,
             'owners': 2,
             'locations': 1,
             'helpers_wanted': 4,
            })

        self.assertEqual(data['helper_totals'],
            {'helpers_provided': 4,
             'distinct_helpers': 2,
             'helpers_cancelled': 1,
            })
