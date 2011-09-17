#-*- x-counterpart: ../src/hanabi/app.py; -*-
import pytest
from hanabi import Application
from werkzeug.test import Client
from werkzeug import Response


class DemoWSGIApp(Application):
    package = 'hanabi.examples.wsgi'


class DemoApp(Application):
    package = 'hanabi.examples.werkzeug'


def pytest_generate_tests(metafunc):
    if 'client' in metafunc.funcargnames:
        metafunc.addcall(funcargs=dict(client=Client(
            DemoWSGIApp.create_app(), Response)))
        metafunc.addcall(funcargs=dict(client=Client(
            DemoApp.create_app(), Response)))


def test_create_app(client):
    with pytest.raises(KeyError):
        client.get('/does/not/exist')


def test_configure_controllers():
    application = DemoWSGIApp.create_app()
    assert set(application.controllers.keys()) == set([
        ('index', 'index'), ('hello', 'world'), ('hello', 'index')])


def test_redirect_trailing_slashes(client):
    response = client.get('/hello/world/')
    assert response.status_code == 302


def test_dispatch_to_module_index(client):
    response = client.get('/')
    assert response.data == 'Index Index!'


def test_dispatch_to_index_class(client):
    response = client.get('/hello')
    assert response.data == 'Hello Index!'


def test_dispatch_to_named_class(client):
    response = client.get('/hello/world')
    assert response.data == 'Hello World!'

def test_reserved_controller_registration():
    app = DemoApp()
    with pytest.raises(ValueError):
        app.register_controller('static', 'Index', dict)
