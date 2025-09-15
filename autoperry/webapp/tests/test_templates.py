
from django.template import Template
from django.template.exceptions import TemplateSyntaxError
from django.template.loader import get_template
from django.test import TestCase


import os


"""
Test that every template is at last syntactically correct
"""

class TemplateTestCase(TestCase):


    def test_templates(self):

        os.chdir('webapp/templates')
        for root, dirs, files in os.walk("webapp"):
            for file in files:
                name = os.path.join(root, file)
                with self.subTest(name):
                    try:
                        template = get_template(name)
                    except Exception as e:
                         self.fail("Template error - '" + str(e) + "'" + " in " + name)
