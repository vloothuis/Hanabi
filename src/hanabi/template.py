#-*- x-counterpart: ../../tests/test_template.py; -*-
import os

from werkzeug import BaseResponse

from .app import Controller


class TemplateController(Controller):
    """ A controller that uses a template to render a response

    The template name is automatically inferred from the module and class name.

    """

    def dispatch(self, request, *args, **kwargs):
        data = self.index(request, *args, **kwargs)
        return self.render_response(request, data)

    def render_response(self, request, data):
        """Render the given data to a response.

        The data is rendered using a template when it is a dictionary (or
        subclass). A template is looked up using the module and class name.
        This is illustrated by the example below:

        fancymodule.FancyClass => ../templates/fancymodule/fancyclass.html

        In case the data argument is not a dictionary it is returned as is.
        This can be used to just pass in response objects etc. without needing
        to check them.
        """
        if isinstance(data, BaseResponse):
            return data

        modulename = self.__module__.rsplit('.', 1)[-1]
        classname = self.__class__.__name__.lower()

        template_extension = '.html'
        content_type = 'text/html'
        if request.is_ajax():
            if request.accept_mimetypes.accept_javascript:
                # Render JS template
                template_extension = '.js'
                content_type = 'application/javascript'

        template_name = os.path.join(modulename, classname + template_extension)
        template = self.app.templates.get_template(template_name)
        return template.render(**data)
