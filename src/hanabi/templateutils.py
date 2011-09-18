#-*- x-counterpart: ../../tests/test_templateutils.py; -*-
import shutil
import tempfile
import hashlib
import os
import re
import itertools
from jinja2 import Markup

class URLFor(object):

    def __init__(self, application):
        self.app = application

    def __call__(self, controller_path, *args):
        args = map(str, args)
        modulename, classname = controller_path.lower().split('.')
        if (modulename, classname) not in self.app.controllers:
            raise KeyError('Controller: %s in module: %s is not registered.' %
                               (classname, modulename))
        return '/' + '/'.join(itertools.chain([modulename, classname], args))


# Store the escape patterns as a list to make sure the order is determined
JS_ESCAPE_PATTERNS = (
    ('\\', '\\\\'),
    ('</', r'<\/'),
    ('\r\n', r'\n'),
    ('\n', r'\n'),
    ('\r', r'\n'),
    ('"', r'\"'),
    ("'", r"\'"))
JS_ESCAPE_MAPPING = dict(JS_ESCAPE_PATTERNS)
JS_REPLACEMENT_RE = re.compile(
    '(' + '|'.join([re.escape(p) for p, r in JS_ESCAPE_PATTERNS]) + ')')

def js_escape(value):
    if value:
        def replace_js_pattern(match):
            return JS_ESCAPE_MAPPING[match.group(0)]
        # Convert to unicode to get rid of Markup objects
        value = unicode(value)
        value = JS_REPLACEMENT_RE.sub(replace_js_pattern, value)
    return value

# Static helpers, look in the static dir, append cache header ?121212 (mtime / app version)
# image_tag
# favicon_link_tag
# javascript_include_tag 'file.js', 'name.js', cache_as='blah.js'
# stylesheet_link_tag
# add profiler

class ResourceHelper(object):
    """A base class for helpers that need to work with static resources.

    Static resources are things like Javascript or CSS files. This base class
    makes it easy to write code that automatically concatenates the resources
    under a cache friendly name.
    """

    resource_type = ''
    extension = ''

    def __init__(self, app):
        self.app = app

    def resource_urls(self, *resources):
        """Returns the URL's for the given resources.

        In development mode it returns a list of several files.

        In production mode it will concatenate all resources and give the
        resulting file a unique name based on the resource names, resource type
        and resource contents. This makes it possible to cache the concatenated
        resources indefinitely.
        """
        if self.app.debug_mode:
            urls = []
            for resource in resources:
                url = '/static/'
                if self.resource_type:
                    url += self.resource_type + '/'
                urls.append(url + resource)
            return urls

        try:
            return self._cached_resource_urls
        except AttributeError:
            pass
        # Create a hash for all the resources. This will be used as the name of
        # the concatenated file.
        hash = hashlib.md5(self.resource_type)
        map(hash.update, resources)

        static_dir = os.path.join(self.app.package_dir, 'static')

        concat_fp, concat_temp = tempfile.mkstemp()
        concat_file = os.fdopen(concat_fp, 'w')

        for resource in resources:
            path = os.path.join(static_dir, self.resource_type, resource)
            if not os.path.exists(path):
                raise ValueError('No resource named: %s found at: %s' %
                                 (resource, path))
            with open(path) as resource_file:
                data = resource_file.read()
                hash.update(data)
                concat_file.write(data)
                concat_file.write('\n')
        concat_file.close()

        cache_dir = os.path.join(static_dir, '_cache')
        if not os.path.exists(cache_dir):
            os.mkdir(cache_dir)
        concat_name = hash.hexdigest() + self.extension
        concat_path = os.path.join(cache_dir,  concat_name)
        shutil.move(concat_temp, concat_path)

        self._cached_resource_urls = ['/static/_cache/' + concat_name]
        return self._cached_resource_urls

    def __call__(self, *resources):
        raise NotImplementedError


class JavascriptInclude(ResourceHelper):
    """Instances of this class can be used to generate Javascript script tags.

    The script tags include the specified resources. It automatically
    concatenates all resources for faster browser delivery.

    It is is intended to be use from within a template. Thus it outputs `safe`
    HTML.
    """
    resource_type = 'javascript'
    extension = '.js'

    def __call__(self, *resources):
        urls = self.resource_urls(*resources)
        html = [u'<script type="text/javascript" src="%s"></script>' % url
                for url in urls]
        return Markup(u''.join(html))
