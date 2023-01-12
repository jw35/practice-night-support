from django.middleware.common import BrokenLinkEmailsMiddleware

class MyBrokenLinkEmailsMiddleware(BrokenLinkEmailsMiddleware):

    """
    Subclass of the standard 'BrokenLinkEmailsMiddleware' that additionally
    ignores ann non-internal requests
    """

    def is_ignorable_request(self, request, uri, domain, referer):
        """
        Return True if the given request *shouldn't* notify the site managers
        according to project settings or in situations outlined by the inline
        comments.
        """

        # Ignore non-internal requests
        if not self.is_internal_request(domain, referer):
            return True;

        # Otherwise devolve to the standard code
        return BrokenLinkEmailsMiddleware.is_ignorable_request(self, request, uri, domain, referer)
