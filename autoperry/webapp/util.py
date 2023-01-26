
from django.template.loader import render_to_string
from django.core.mail import send_mail
from django.contrib.auth.decorators import user_passes_test
from django.contrib.auth import REDIRECT_FIELD_NAME
from django.contrib.auth.tokens import PasswordResetTokenGenerator

from custom_user.models import User

import logging
logger = logging.getLogger(__name__)

def send_template_email(to,template,context):

    """
    Construct an email from the supplied template path and context
    and send it to the user
    """

    message = render_to_string(f"webapp/email/{template}-message.txt", context).strip()
    subject = render_to_string(f"webapp/email/{template}-subject.txt", context).strip()
    if isinstance(to, User):
        to.email_user(subject, message)
        logger.info(f'Emailed user {to} {to.email} "{subject}"')
    else:
        send_mail(subject, message, None, [to])
        logger.info(f'Emailed address {to} "{subject}"')

def login_required(function=None, redirect_field_name=REDIRECT_FIELD_NAME, login_url=None):

    """
    Copy of login_required from django.contrib.auth.decorators with condition
    expanded to include email_validated and not suspended
    """

    actual_decorator = user_passes_test(
        lambda u: u.is_authenticated and u.email_validated and not u.suspended,
        login_url=login_url,
        redirect_field_name=redirect_field_name,
    )
    if function:
        return actual_decorator(function)
    return actual_decorator

class EmailVerificationTokenGenerator(PasswordResetTokenGenerator):

    """
    MAke a customised hash that includes user.email_validated
    """
    def _make_hash_value(self, user, timestamp):
        return (
                str(user.email_validated) + str(user.pk) + str(timestamp)
        )
