#-*- x-counterpart: ../src/hanabi/rest.py; -*-
import pytest
from hanabi import RESTController
from werkzeug.test import EnvironBuilder
from werkzeug import Response
from werkzeug.exceptions import MethodNotAllowed

class App(object):
    version = 1.2

def test_disallow_methods():
    class NothingAllowed(RESTController):
        pass

    controller = NothingAllowed(None)
    with pytest.raises(MethodNotAllowed):
        response = controller.dispatch(EnvironBuilder().get_request(), None)


def test_json_conversion():
    class App(object):
        version = 1.2

    class JSONTest(RESTController):
        allowed_methods = ('GET',)

        def list(self, request):
            return {'artists': ['Hans Zimmer', 'Miles Davis']}

    controller = JSONTest(App())
    response = controller.dispatch(EnvironBuilder().get_request(), None)
    assert response.content_type == 'application/json'
    assert response.data == '{"artists": ["Hans Zimmer", "Miles Davis"]}'


def test_dispatch_to_methods():
    class JSONTest(RESTController):

        def list(self, request):
            return {'method': 'list'}

        def get(self, request, id):
            return {'method': 'get', 'id': id}

        def delete(self, request, id):
            return {'method': 'delete', 'id': id}

        def update(self, request, id):
            return {'method': 'update', 'id': id}

        def create(self, request):
            return {'method': 'create'}

    controller = JSONTest(App())

    checks = [('GET', '', '{"method": "list"}'),
              ('GET', 'test', '{"method": "get", "id": "test"}'),
              ('POST', '', '{"method": "create"}'),
              ('DELETE', 'test', '{"method": "delete", "id": "test"}'),
              ('PUT', 'test', '{"method": "update", "id": "test"}')]
    for method, path, expected in checks:
        response = controller.dispatch(
            EnvironBuilder(method=method).get_request(), path)
        assert response.response == [expected]


class test_disallow_all_methods_by_default():
    controller = RESTController(App())

    checks = [('GET', ''),
              ('GET', 'test'),
              ('POST', ''),
              ('DELETE', 'test'),
              ('PUT', 'test'),
              ('CARROT', '')]
    for method, path in checks:
        with pytest.raises(MethodNotAllowed):
            controller.dispatch(
                EnvironBuilder(method=method).get_request(), path)


def test_disallowed_post_to_resource():
    # POST is only allowed on collections
    controller = RESTController(App())
    with pytest.raises(MethodNotAllowed):
        controller.dispatch(
            EnvironBuilder(method='POST').get_request(), 'test')


def test_etag_generation():
    req = None
    tagdata1 = [req, 1, 'testing', {'test': 'value'}]
    tagdata2 = [req, 1, 'TESTING', {'test': 'value'}]

    controller = RESTController(App())
    tag1 = controller.etag(*tagdata1)
    tag2 = controller.etag(*tagdata2)
    # Tag 1 and 2 must be different
    assert tag1 != tag2
    # Tags must be the same for the same data
    assert tag1 == controller.etag(*tagdata1)


def test_etag_uses_app_version():
    req = None
    app = App()
    controller = RESTController(app)
    tag1 = controller.etag('test')
    app.version = 2.0
    tag2 = controller.etag('test')
    # Tag 1 and 2 must be different
    assert tag1 != tag2


def test_get_response():
    class GETTest(RESTController):

        def get(self, request, id):
            return {'test': 'testing'}

    controller = GETTest(App)
    response = controller.dispatch(
            EnvironBuilder().get_request(), 'id')
    # Must have a proper ETag
    assert response.status_code == 200
    assert response.headers['ETag'] == '"56765472680401499c79732468ba4340"'
    # Default caching policy
    assert response.headers['Cache-Control'] == 'must-revalidate'
    assert response.response == ['{"test": "testing"}']


def test_get_with_matching_etag():
    class GETTest(RESTController):

        def get(self, request, id):
            return {'test': 'testing'}

    controller = GETTest(App)
    env = EnvironBuilder(
        headers=[('If-None-Match', '"56765472680401499c79732468ba4340"')])
    response = controller.dispatch(env.get_request(), 'id')
    assert response.status_code == 304
    assert response.headers['ETag'] == '"56765472680401499c79732468ba4340"'
    assert response.headers['Cache-Control'] == 'must-revalidate'
    assert response.response == []


def test_response_with_none_and_etag():
    class GETTest(RESTController):
        pass

    controller = GETTest(App)
    env = EnvironBuilder(
        headers=[('If-None-Match', '"56"')])
    response = controller.response(env.get_request(), None, etag='56')
    assert response.status_code == 304
    assert response.headers['ETag'] == '"56"'


def test_response_with_none_without_etag():
    class GETTest(RESTController):
        pass

    controller = GETTest(App)
    env = EnvironBuilder(
        headers=[('If-None-Match', '"56"')])
    with pytest.raises(TypeError):
         controller.response(env.get_request(), None)


def test_custom_response():
    resp = Response()
    class GETTest(RESTController):

        def get(self, request, id):
            return resp

    controller = GETTest(App)
    response = controller.dispatch(EnvironBuilder().get_request(), 'id')
    assert resp is response

def test_single_get_when_multiple_etags_and_specific_etag():
    pass


def test_response_with_custom_etag():
    pass


def test_response_with_custom_caching_policy():
    pass
