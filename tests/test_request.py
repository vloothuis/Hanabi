#-*- x-counterpart: ../src/hanabi/request.py; -*-
from hanabi import request
from werkzeug.test import EnvironBuilder


class TestMIMEAccept(object):

    def test_accept_javascript(self):
        accept = request.MIMEAccept([('text/javascript', 1)])
        assert accept.accept_javascript

    def test_does_not_accept_javascript(self):
        accept = request.MIMEAccept([('text/html', 1)])
        assert not accept.accept_javascript


class TestRequest(object):

    def test_is_ajax(self):
        builder = EnvironBuilder(headers=[('X_REQUESTED_WITH', 'XMLHttpRequest')])
        req = request.Request(builder.get_environ())
        assert req.is_ajax()

    def test_is_not_ajax(self):
        builder = EnvironBuilder()
        req = request.Request(builder.get_environ())
        assert not req.is_ajax()

    def test_accept_mimetypes_uses_custom(self):
        builder = EnvironBuilder()
        req = request.Request(builder.get_environ())
        assert isinstance(req.accept_mimetypes, request.MIMEAccept)
