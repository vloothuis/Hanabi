from werkzeug.exceptions import MethodNotAllowed

from .template import TemplateController


class FormController(TemplateController):
    """A base class for controllers that need to process forms.

    This class helps with form handling by calling the `form` method. That
    method needs to be overridden with one that returns a form object. The next
    step in the dispatch chain is to call either the `view` or `process` method.

    These methods get the normal `request` and optional arguments but they also
    receive the form. The dispatcher calls the `view` method if the request
    method is GET. The `process` method is called for POST requests.

    The return value from either method can be a dictionary or a response
    object. In the case a dictionary is returned it will be rendered using the
    template. See the `TemplateController` class for more info.
    """
    def form(self, request, *args, **kwargs):
        raise NotImplementedError

    def view(self, request, form, *args, **kwargs):
        raise NotImplementedError

    def process(self, request, form, *args, **kwargs):
        raise NotImplementedError

    def dispatch(self, request, *args, **kwargs):
        form = self.form(request, *args, **kwargs)
        req_method = request.method.upper()

        if req_method == 'GET':
            data = self.view(request, form, *args, **kwargs)
        elif req_method == 'POST':
            data = self.process(request, form, *args, **kwargs)
        else:
            raise MethodNotAllowed

        return self.render_response(request, data)

