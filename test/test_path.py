import pytest
import os

from groove import path
from groove.exceptions import ConfigurationError, ThemeMissingException
from groove.webserver import themes


@pytest.mark.parametrize('root', ['/dev/null/missing', None])
def test_missing_media_root(monkeypatch, root):
    broken_env = {k: v for (k, v) in os.environ.items()}
    broken_env['MEDIA_ROOT'] = root
    monkeypatch.setattr(os, 'environ', broken_env)
    with pytest.raises(ConfigurationError):
        path.media_root()


def test_static(monkeypatch):
    assert path.static('foo')
    assert path.static('foo', theme=themes.load_theme('default_theme'))


def test_missing_theme_root(monkeypatch):
    broken_env = {k: v for (k, v) in os.environ.items()}
    broken_env['THEMES_PATH'] = '/dev/null/enoexist'
    monkeypatch.setattr(os, 'environ', broken_env)
    with pytest.raises(ConfigurationError):
        path.themes_root()


def test_theme_no_path():
    with pytest.raises(ThemeMissingException):
        path.theme('nope')


def test_database_default(env):
    assert path.database()


def test_database(env):
    assert env['DATABASE_PATH'] in str(path.database().absolute())
