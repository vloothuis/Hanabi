#-*- x-counterpart: ../src/hanabi/templateutils.py; -*-
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
