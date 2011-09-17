#-*- x-counterpart: ../src/hanabi/template.py; -*-
from hanabi import TemplateController
from hanabi.request import Request
from werkzeug import BaseResponse
from werkzeug.test import EnvironBuilder

class FakeTemplateEnviron(object):
    def get_template(self, template_name):
        class Template(object):
            def render(self, *args, **kwargs):
                return (template_name, args, kwargs)
        return Template()


class FakeApp(object):
    templates = FakeTemplateEnviron()


class DummyController(TemplateController):
    def index(self, request):
        return {'hello': 'World'}


def test_dispatch():
    controller = DummyController(FakeApp())
    req = Request(EnvironBuilder().get_environ())
    response = controller.dispatch(req)
    assert response[0] == 'test_template/dummycontroller.html'
    assert response[1] == ()
    assert response[2] == {'hello': 'World'}

def test_render_response_passthrough_response_objects():
    class ResponseController(TemplateController):
        def index(self, request):
            return BaseResponse('Testing')
    controller = ResponseController(FakeApp())
    req = Request(EnvironBuilder().get_environ())
    response = controller.dispatch(req)
    assert response.response == ['Testing']

def test_render_ajax_with_javascript():
    controller = DummyController(FakeApp())
    req = Request(EnvironBuilder(
        headers=[('X_REQUESTED_WITH', 'XMLHttpRequest'),
                 ('ACCEPT', 'text/javascript')]).get_environ())
    response = controller.render_response(req, {'test': 'data'})
    assert response[0] == 'test_template/dummycontroller.js'
    assert response[2] == {'test': 'data'}

def test_render_ajax_with_html():
    controller = DummyController(FakeApp())
    req = Request(EnvironBuilder(
        headers=[('X_REQUESTED_WITH', 'XMLHttpRequest'),
                 ('ACCEPT', 'text/html')]).get_environ())
    response = controller.render_response(req, {'test': 'data'})
    assert response[0] == 'test_template/dummycontroller.html'
    assert response[2] == {'test': 'data'}

def test_render():
    controller = DummyController(FakeApp())
    req = Request(EnvironBuilder().get_environ())
    response = controller.render_response(req, {'test': 'data'})
    assert response[0] == 'test_template/dummycontroller.html'
    assert response[2] == {'test': 'data'}
