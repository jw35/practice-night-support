
from django.template.loader import render_to_string
from django.core.mail import send_mail

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
	else:
		send_mail(subject, message, None, [to])
	logger.info(f'Emailed {to} "{subject}"')
