from django.conf import settings
from django.middleware.common import BrokenLinkEmailsMiddleware
from django.http import HttpResponseForbidden
from django.urls import is_valid_path

from urllib.parse import urlparse

class MyBrokenLinkEmailsMiddleware(BrokenLinkEmailsMiddleware):

    """
    Subclass of the standard 'BrokenLinkEmailsMiddleware' that additionally
    ignores ann non-internal requests
    """

    def is_ignorable_request(self, request, uri, domain, referer):
        """
        Return True if the given request came from one of our
        pages - not from some other server and not apparently
        from a non-existent age on our server.
        """

        # Nothing we can do unless referer is set
        if referer:


            # Ignore requests from elsewhere
            if not self.is_internal_request(domain, referer):
                return True;

            # Ignore requests where the referer (if necessary with a
            # trailing slash added) isn't actually one of our URLs
            referer_path = urlparse(referer).path
            urlconf = getattr(request, "urlconf", None)

            ours = is_valid_path(referer_path, urlconf)
            if not ours and settings.APPEND_SLASH and not referer_path.endswith("/"):
                ours = is_valid_path("%s/" % referer_path, urlconf)

            if not ours:
                return True

        # Otherwise devolve to the standard code
        return BrokenLinkEmailsMiddleware.is_ignorable_request(self, request, uri, domain, referer)

# Copied in a hurry from https://medium.com/@chko/how-to-block-malicious-ips-in-django-with-middleware-c60651963b64
# List of blocked IP addresses
BLOCKED_IPS = ["107.174.244.120", "196.251.70.5", "196.251.70.8"]

class BlockIPMiddleware:

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Get client IP
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[-1].strip()
        else:
            ip = request.META.get('REMOTE_ADDR')

        if ip in BLOCKED_IPS:
            return HttpResponseForbidden("Access Denied")

        return self.get_response(request)
