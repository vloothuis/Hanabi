#-*- x-counterpart: ../../tests/test_request.py; -*-
from werkzeug.http import parse_accept_header
from werkzeug import Request as BaseRequest
from werkzeug.datastructures import MIMEAccept as BaseMIMEAccept
from werkzeug import cached_property

JAVASCRIPT_MIMETYPES = ('text/javascript', 'application/x-ecmascript',
                        'application/javascript', 'application/ecmascript')

class MIMEAccept(BaseMIMEAccept):

    @property
    def accept_javascript(self):
        """True if this object accepts Javascript."""
        for mime in JAVASCRIPT_MIMETYPES:
            if mime in self:
                return True
        return False


class Request(BaseRequest):
    """Request wraps the WSGI environ.

    This subclasses Werkzeug's basic Request wrapper to add some functionality.
    """

    def is_ajax(self):
        return self.environ.get('HTTP_X_REQUESTED_WITH') == 'XMLHttpRequest'

    @cached_property
    def accept_mimetypes(self):
        """List of mimetypes this client supports as `~werkzeug.datastructures.MIMEAccept` object.
        """
        # This method is overridden to use the customized MIMEAccept class
        return parse_accept_header(self.environ.get('HTTP_ACCEPT'), MIMEAccept)
