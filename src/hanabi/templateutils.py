#-*- x-counterpart: ../../tests/test_templateutils.py; -*-
import re
import itertools

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
