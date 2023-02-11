
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


        well_before = start - timedelta(hours=2)
        before = start - timedelta(hours=1)
        just_started = start + timedelta(minutes=5)
        middle = start + timedelta(hours=1)
        almost_finished = end - timedelta(minutes=5)
        after = end+timedelta(hours=1)
        well_after = end+timedelta(hours=2)

        cls.event_spec = {
            'before':      [well_before,     before],
            'upto_start':  [before,          start],
            'into':        [before,          middle],
            'upto_end':    [before,          end],
            'contains':    [before,          after],
            'first_part':  [start,           middle],
            'all':         [start,           end],
            'from_start':  [start,           after],
            'within':      [just_started,    almost_finished],
            'last_part':   [middle,          end],
            'out_of':      [middle,          after],
            'from_end':    [end,             after],
            'after':       [after,           well_after],
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


    def test_event_shouldnt_clash(self):

        self.assertFalse(event_clash_error(*self.event_spec['before'], self.location))
        self.assertFalse(event_clash_error(*self.event_spec['upto_start'], self.location))
        self.assertFalse(event_clash_error(*self.event_spec['from_end'], self.location))
        self.assertFalse(event_clash_error(*self.event_spec['after'], self.location))

    def test_event_should_clash(self):

        self.assertTrue(event_clash_error(*self.event_spec['into'], self.location))
        self.assertTrue(event_clash_error(*self.event_spec['upto_end'], self.location))
        self.assertTrue(event_clash_error(*self.event_spec['contains'], self.location))

        self.assertTrue(event_clash_error(*self.event_spec['first_part'], self.location))
        self.assertTrue(event_clash_error(*self.event_spec['all'], self.location))
        self.assertTrue(event_clash_error(*self.event_spec['from_start'], self.location))

        self.assertTrue(event_clash_error(*self.event_spec['within'], self.location))
        self.assertTrue(event_clash_error(*self.event_spec['last_part'], self.location))

        self.assertTrue(event_clash_error(*self.event_spec['out_of'], self.location))

    def test_event_elsewhere(self):

        self.assertFalse(event_clash_error(*self.event_spec['before'], self.elsewhere))

        self.assertFalse(event_clash_error(*self.event_spec['upto_start'], self.elsewhere))
        self.assertFalse(event_clash_error(*self.event_spec['into'], self.elsewhere))
        self.assertFalse(event_clash_error(*self.event_spec['upto_end'], self.elsewhere))
        self.assertFalse(event_clash_error(*self.event_spec['contains'], self.elsewhere))

        self.assertFalse(event_clash_error(*self.event_spec['first_part'], self.elsewhere))
        self.assertFalse(event_clash_error(*self.event_spec['all'], self.elsewhere))
        self.assertFalse(event_clash_error(*self.event_spec['from_start'], self.elsewhere))

        self.assertFalse(event_clash_error(*self.event_spec['within'], self.elsewhere))
        self.assertFalse(event_clash_error(*self.event_spec['last_part'], self.elsewhere))

        self.assertFalse(event_clash_error(*self.event_spec['out_of'], self.elsewhere))

        self.assertFalse(event_clash_error(*self.event_spec['from_end'], self.elsewhere))

        self.assertFalse(event_clash_error(*self.event_spec['after'], self.elsewhere))


    def test_volounteering(self):

        # Make some test events

        test_event = {}
        for key in self.event_spec.keys():
            test_event[key] = Event.objects.create(
                start=self.event_spec[key][0],
                end=self.event_spec[key][1],
                location=self.location,
                helpers_required=2,
                owner=self.live,
                contact_address=None,
                notes=key,
                alerts=True)

        self.assertFalse(volunteer_clash_error(self.live, test_event['before']))
        self.assertFalse(volunteer_clash_error(self.live, test_event['upto_start']))
        self.assertFalse(volunteer_clash_error(self.live, test_event['from_end']))
        self.assertFalse(volunteer_clash_error(self.live, test_event['after']))

        self.assertTrue(volunteer_clash_error(self.live, test_event['into']))
        self.assertTrue(volunteer_clash_error(self.live, test_event['upto_end']))
        self.assertTrue(volunteer_clash_error(self.live, test_event['contains']))
        self.assertTrue(volunteer_clash_error(self.live, test_event['first_part']))
        self.assertTrue(volunteer_clash_error(self.live, test_event['all']))
        self.assertTrue(volunteer_clash_error(self.live, test_event['from_start']))
        self.assertTrue(volunteer_clash_error(self.live, test_event['within']))
        self.assertTrue(volunteer_clash_error(self.live, test_event['last_part']))
        self.assertTrue(volunteer_clash_error(self.live, test_event['out_of']))





