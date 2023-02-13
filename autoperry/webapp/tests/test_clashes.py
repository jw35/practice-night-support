
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from django.core import mail
from django.test import TestCase
from django.utils import timezone

from webapp.models import Event

from datetime import datetime, timedelta
import re

from webapp.util import event_clash_error, volunteer_clash_error

class ClashesTestCase(TestCase):

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
            approved=timezone.now())

        cls.owner = user_model.objects.create_user(
            email='owner@autoperry.com',
            password='password',
            first_name='Geoff',
            last_name='Owner',
            tower='Little Shelford',
            email_validated=timezone.now(),
            approved=timezone.now())

        start = datetime(1960, 3, 5, 12, 00)
        end = start + timedelta(hours=2)

        before = start - timedelta(hours=2)
        just_before = start - timedelta(hours=1)
        just_started = start + timedelta(minutes=5)
        almost_finished = end - timedelta(minutes=5)
        just_after = end+timedelta(hours=1)
        after = end+timedelta(hours=2)

        cls.event_spec = {
            'before':      [before,          just_before],
            'upto_start':  [before,          start],
            'into':        [before,          just_started],
            'upto_end':    [before,          end],
            'contains':    [before,          after],
            'first_part':  [start,           just_started],
            'all':         [start,           end],
            'from_start':  [start,           after],
            'within':      [just_started,    almost_finished],
            'last_part':   [almost_finished, end],
            'out_of':      [almost_finished, after],
            'from_end':    [end,             after],
            'after':       [just_after,      after],
        }

        cls.event_expected = {
            'before':      False,
            'upto_start':  False,
            'into':        True,
            'upto_end':    True,
            'contains':    True,
            'first_part':  True,
            'all':         True,
            'from_start':  True,
            'within':      True,
            'last_part':   True,
            'out_of':      True,
            'from_end':    False,
            'after':       False,
        }

        cls.location = 'Little Shelford'
        cls.elsewhere = 'Whittlesford'

        cls.event = Event.objects.create(
            start=start,
            end=end,
            location=cls.location,
            helpers_required=2,
            owner=cls.live,
            contact_address=None,
            notes='Ab C#',
            alerts=True)

        cls.event.helpers.add(cls.live)


    def test_event(self):

        for key in self.event_spec.keys():
            with self.subTest(key):
                self.assertEqual(bool(event_clash_error(*self.event_spec[key], self.location)), self.event_expected[key])


    def test_event_elsewhere(self):

        for key in self.event_spec.keys():
            with self.subTest(key):
                self.assertEqual(bool(event_clash_error(*self.event_spec[key], self.elsewhere)), False)


    def test_volounteering(self):

        for key in self.event_spec.keys():
            with self.subTest(key):
                event = Event.objects.create(
                    start=self.event_spec[key][0],
                    end=self.event_spec[key][1],
                    location=self.location,
                    helpers_required=2,
                    owner=self.live,
                    contact_address=None,
                    notes=key,
                    alerts=True)

                self.assertEqual(bool(volunteer_clash_error(self.live, event)), self.event_expected[key])




