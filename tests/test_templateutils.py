#-*- x-counterpart: ../src/hanabi/templateutils.py; -*-
import time
import shutil
import tempfile
import os
import pytest
from hanabi import templateutils


def test_urlfor_without_registered():
    class FakeApp(object):
        controllers = {}

    url_for = templateutils.URLFor(FakeApp())
    with pytest.raises(KeyError):
        url_for('peanut.Butter')

def test_url_for_with_args():
    class FakeApp(object):
        controllers = {('peanut', 'butter')}

    url_for = templateutils.URLFor(FakeApp())
    url = url_for('peanut.Butter', 'jam', 'cheese')
    assert url == '/peanut/butter/jam/cheese'



def test_js_escape():
    pairs = [(r'test\ing', r'test\\ing'),
             ('</tag>', r'<\/tag>'),
             ('test \r\n line feeds', r'test \n line feeds'),
             ('test \n line feed', r'test \n line feed'),
             ('return \r', r'return \n'),
             ('qoute "', r'qoute \"'),
             ("single quote '", r"single quote \'")]
    for value, expected in pairs:
        assert templateutils.js_escape(value) == expected



class TestResourceHelper(object):

    def setup_method(self, method):
        self.package_dir = tempfile.mkdtemp()
        class FakeApp(object):
            debug_mode = False
            package_dir = self.package_dir
        self.static_dir = os.path.join(self.package_dir, 'static')
        os.mkdir(self.static_dir)
        self.app = FakeApp()
        self.resource_helper = templateutils.ResourceHelper(self.app)

    def teardown_method(self, method):
        shutil.rmtree(self.package_dir)

    def test_concat_resources(self):
        for text in ('a', 'b', 'c'):
            with open(os.path.join(self.static_dir, text), 'w') as f:
                f.write(text)
        urls = self.resource_helper.resource_urls('a', 'c')
        assert len(urls) == 1  # Concatenation should return one result
        concatenated = os.path.join(self.package_dir, urls[0].strip('/'))
        with open(concatenated) as f:
            assert f.read() == 'a\nc\n'

    def test_list_resources_in_debug(self):
        self.app.debug_mode = True
        urls = self.resource_helper.resource_urls('a', 'b', 'c')
        assert urls == ['/static/a', '/static/b', '/static/c']

    def test_run_once(self):
        for text in ('a'):
            with open(os.path.join(self.static_dir, text), 'w') as f:
                f.write(text)
        urls1 = self.resource_helper.resource_urls('a')
        shutil.rmtree(self.static_dir)
        urls2 = self.resource_helper.resource_urls('a')
        assert urls1 == urls2

    def test_unique_name_for_resources(self):
        for text in ('a', 'b'):
            with open(os.path.join(self.static_dir, text), 'w') as f:
                f.write(text)
        urls1 = self.resource_helper.resource_urls('a', 'b')
        with open(os.path.join(self.static_dir, 'b'), 'w') as f:
            f.write('c')
        another_helper = templateutils.ResourceHelper(self.app)
        urls2 = another_helper.resource_urls('a', 'b')
        assert urls1 != urls2

    def test_cache_per_resource_set(self):
        for text in ('a', 'b'):
            with open(os.path.join(self.static_dir, text), 'w') as f:
                f.write(text)
        urls1 = self.resource_helper.resource_urls('a', 'b')
        urls2 = self.resource_helper.resource_urls('a')
        assert urls1 != urls2

    def test_check_for_non_existing_files(self):
        with pytest.raises(ValueError):
            self.resource_helper.resource_urls('a')

    def test_include_extension(self):
        self.resource_helper.extension = '.js'
        for text in ('a', 'b'):
            with open(os.path.join(self.static_dir, text), 'w') as f:
                f.write(text)
        urls = self.resource_helper.resource_urls('a', 'b')
        assert urls[0][-3:] == '.js'

    def test_use_resource_type(self):
        self.resource_helper.resource_type = 'js'
        js_dir = os.path.join(self.static_dir, 'js')
        os.mkdir(js_dir)
        for text in ('a', 'b'):
            with open(os.path.join(js_dir, text), 'w') as f:
                f.write(text)
        # No error means it found the files
        self.resource_helper.resource_urls('a', 'b')

    def test_use_resource_type_in_debug_mode(self):
        self.app.debug_mode = True
        self.resource_helper.resource_type = 'js'
        js_dir = os.path.join(self.static_dir, 'js')
        os.mkdir(js_dir)
        for text in ('a', 'b'):
            with open(os.path.join(js_dir, text), 'w') as f:
                f.write(text)
        assert self.resource_helper.resource_urls('a', 'b') == [
            '/static/js/a', '/static/js/b']


class TestJavascripInclude(object):

    def setup_method(self, method):
        self.package_dir = tempfile.mkdtemp()
        class FakeApp(object):
            debug_mode = False
            package_dir = self.package_dir
        self.js_dir = os.path.join(self.package_dir, 'static', 'javascript')
        os.makedirs(self.js_dir)
        self.app = FakeApp()
        self.resource_helper = templateutils.JavascriptInclude(self.app)

    def test_script_tag(self):
        for text in ('a', 'b'):
            with open(os.path.join(self.js_dir, text), 'w') as f:
                f.write(text)
        assert self.resource_helper('a', 'b') == (
            '<script type="text/javascript"'
            ' src="/static/_cache/9b1757704f9f7cbf3672b6ca786cc6a1.js">'
            '</script>')
