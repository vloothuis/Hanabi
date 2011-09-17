#-*- x-counterpart: ../../tests/test_application.py; -*-
import logging
import importlib
import os
import sys
import tempfile
from glob import glob
from werkzeug import Response
from .request import Request
from werkzeug.exceptions import HTTPException
from werkzeug.serving import run_simple
from werkzeug.debug import DebuggedApplication
from werkzeug.wsgi import SharedDataMiddleware
from jinja2 import Environment, PackageLoader, FileSystemBytecodeCache

from . import templateutils


# /wiki => wiki.py Index.index
# /wiki/12 => wiki.py Index.index(12)
# /wiki/list => wiki.py List.index
# /wiki/page/45/edit => wiki.py Page.index(45/edit)

def guess_autoescape(template_name):
    """Called by Jinja2 to enable auto escaping."""
    if template_name is not None:
        if template_name.endswith('.js'):
            return False
    return True

class WSGIController(object):

    def __init__(self, app):
        self.app = app

    def __call__(self, environ, start_response, *args, **kwargs):
        return self.index(environ, start_response)

    def index(self, enviorn, start_response):
        pass


class Application(object):
    controller_module = '.controllers'
    package = None

    def __init__(self):
        self.controllers = {}
        # Setup the template loader with some defaults
        tmp = os.path.join(tempfile.gettempdir(), self.package + '-template-cache')
        if not os.path.exists(tmp):
            os.mkdir(tmp)
        self.templates = Environment(
            loader=PackageLoader(self.package, 'templates'),
            bytecode_cache=FileSystemBytecodeCache(),
            autoescape=guess_autoescape,
            extensions=['jinja2.ext.autoescape'])
        self.templates.globals.update(
            url_for=templateutils.URLFor(self))
        self.templates.filters['js_escape'] = templateutils.js_escape

        self.version = self._find_version()

    def _find_version(self):
        package = importlib.import_module(self.package)
        try:
            return package.__version__
        except AttributeError:
            logging.warning('No __version__ specified for package: %s.'
                            ' Setting is strongly recommended.' % self.package)

    def __call__(self, environ, start_response):
        # No extra trailing slashes allowed
        path_info = environ.get('PATH_INFO', '')
        if path_info != '/' and path_info.endswith('/'):
            return self.redirect(start_response, path_info.rstrip('/'))

        # Create the keys for our controller lookup
        request_path = '/' + path_info.lstrip('/')
        parts = request_path.split('/', 3)
        nr_of_parts = len(parts)
        remaining_path = ''
        if nr_of_parts == 2:
            module_name = parts[1]
            controller_name = 'index'
        elif nr_of_parts == 3:
            module_name, controller_name = parts[1:]
        else:
            module_name, controller_name, remaining_path = parts[1:]

        # Default to the index module for root level access
        if module_name == '':
            module_name = 'index'

        try:
            controller = self.controllers[(module_name, controller_name)]
        except KeyError:
            if controller_name != 'index':
                controller = self.controllers[(module_name, 'index')]
                remaining_path = controller_name + '/' + remaining_path
            else:
                raise

        args = []
        if remaining_path:
            args.append(remaining_path)
        return controller(environ, start_response, *args)

    def redirect(self, start_response, path):
        start_response('302 Found', [('Location', path)])
        return ''

    def register_controller(self, modulename, classname, cls):
        """Register a controller with the application.

        Any existing controller registration will be overridden. The
        registration does make sure the name of both the module or the class
        are not reserved. Currently `static` is disallowed for the module name
        since it would clash with static file serving.
        """
        if modulename == 'static':
            raise ValueError('Modulename: "%s" is reserved.' % modulename)
        self.controllers[(modulename, classname.lower())] = cls(app=self)

    def configure_controllers(self):
        controllers_module = importlib.import_module(self.controller_module, package=self.package)
        controller_dir = os.path.dirname(controllers_module.__file__)

        for controller_file in os.listdir(controller_dir):
            if not controller_file.endswith('.py'):
                continue
            controller_modulename = os.path.splitext(controller_file)[0]
            if controller_modulename == 'static':
                raise ValueError(
                    'A controller module cannot be named static '
                    'since that would clash with static file serving.')
            print controller_modulename
            if controller_modulename.startswith('__'):
                continue
            controller_module = importlib.import_module(
                '%s.%s' % (self.controller_module, controller_modulename),
                package=self.package)
            print 'Scanning module:', controller_modulename
            for obj_name in dir(controller_module):
                obj = getattr(controller_module, obj_name)
                if isinstance(obj, type) and issubclass(obj, WSGIController) and obj.__module__ == controller_module.__name__:
                    print 'Added controller:', obj_name
                    self.register_controller(controller_modulename, obj_name, obj)

    @classmethod
    def create_app(cls, **config):
        app = cls(**config)
        app.configure_controllers()
        return app

    @classmethod
    def run_develop(cls, **config):
        app = cls.create_app(**config)
        package = importlib.import_module(app.package)
        app = SharedDataMiddleware(app, {
            '/static': os.path.join(os.path.dirname(package.__file__), 'static')
        })
        run_simple('localhost', 8080, DebuggedApplication(app, evalex=True), use_reloader=True)


class Controller(WSGIController):

    def dispatch(self, request, *args, **kwargs):
        return self.index(request)

    def __call__(self, environ, start_response, *args, **kwargs):
        request = Request(environ)
        try:
            response = self.dispatch(request, *args, **kwargs)
        except HTTPException, e:
            response = e.get_response(environ)
        if isinstance(response, basestring):
            response = Response(response, content_type='text/html')
        return response(environ, start_response)
