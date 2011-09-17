#-*- x-counterpart: ../../tests/test_rest.py; -*-
import hashlib
import json

from werkzeug.http import quote_etag, parse_etags
from werkzeug.exceptions import MethodNotAllowed
from werkzeug import Response

from .app import Controller
from .caching import conditional_get


class RESTController(Controller):
    """ This class can be used to create RESTful API's.

    It dispatches to methods matching the HTTP request method. The following
    mapping is used.

        GET    /controller    -> list()
        POST   /controller    -> create()
        GET    /controller/id -> get(id)
        DELETE /controller/id -> delete(id)
        PUT    /controller/id -> update(id)

    By default all methods raise a http method not allowed error. Just override
    them to get the behavior that is needed.


    The return value of an overridden method is automatically converted to a
    JSON response.
    """
    cache_policy = conditional_get
    data_encoder = json.JSONEncoder()

    def etag(self, request, *args):
        """Create an ETag for the given arguments.

        All arguments are automatically converted to strings.

        The final ETag also includes the current app version. This is done so
        that a new deployment of the code will be effective immediatly.

        FIXME: AUTHENTICATED USER MUST BE ADDED AS WELL
        """
        hash = hashlib.md5(str(self.app.version))
        # FIXME: hash.update(request.authenticated_user)
        for data in args:
            # Avoid inconsistent hashes because of varying sort order in dicts
            if isinstance(data, dict):
                data = data.items()
                data.sort()
            hash.update(str(data))
        return hash.hexdigest()

    def response(self, request, data, etag=None, cache_policy=None):
        """Renders `data` to a JSON response.

        An ETag may be specified. When it is not specified one will be generated
        based on the data.

        The caching policy can be optionally configured. By default it takes the
        policy from the controller object: `cache_policy`.
        """
        if etag is None and data is not None:
            etag = self.etag(data)
        # FIXME: Check content-type headers
        if data is None:
            if etag is None:
                raise TypeError('response requires an etag when '
                                'the response body is None')
            resp = Response(status=304, content_type='application/json')
        else:
            # Avoid sending the resource when an ETag matches
            request_etags = parse_etags(
                request.environ.get('HTTP_IF_NONE_MATCH'))
            if request_etags.contains(etag):
                 resp = Response(status=304, content_type='application/json')
            # Render the given data to a response object
            else:
                resp = Response(self.data_encoder.encode(data), content_type='application/json')
        resp.headers['ETag'] = quote_etag(etag)
        if cache_policy is None:
            cache_policy = self.cache_policy
        return cache_policy(resp)

    def list(self, request):
        raise MethodNotAllowed

    def create(self, request):
        # FIXME: Set content-location and Location headers
#         (http://bitworking.org/projects/atom/draft-ietf-atompub-protocol-17.
#         html#crwp)
        raise MethodNotAllowed

    def get(self, request, id):
        raise MethodNotAllowed

    def delete(self, request, id):
        # FIXME: No etag
        raise MethodNotAllowed

    def update(self, request, id):
        # FIXME: check etag, if differs return http 412
        raise MethodNotAllowed

    def dispatch(self, request, path=None):
        req_method = request.method

        if req_method == 'PUT' and path:
            data = self.update(request, path)
        elif req_method == 'POST':
            if path:
                raise MethodNotAllowed
            data = self.create(request)
        elif req_method == 'GET':
            if path:
                data = self.get(request, path)
            else:
                data = self.list(request)
        elif req_method == 'DELETE' and path:
            data = self.delete(request, path)
        # Everything failed, so the request must not be valid
        else:
            raise MethodNotAllowed

        # Do automatic conversion for JSON data types
        if isinstance(data, dict) or isinstance(data, list) or data is None:
            return self.response(request, data)

#         if data is None:
#             if method is GET:
#                 return KEEP CACHE
#             elif method is PUT:
#                 return DIFFERS 412

        # Assume it is a response object or something which will be handled
        # higher up
        return data
