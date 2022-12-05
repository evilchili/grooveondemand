import pytest
from groove.webserver import themes
from groove.exceptions import ThemeConfigurationError


def test_load_theme():
    theme = themes.load_theme('default_theme')
    assert theme.name == 'default_theme'
    assert theme.author == 'Theme Author'
    assert theme.author_link == 'link to my soundcloud'
    assert theme.version == '1.3'


def test_load_broken_theme():
    with pytest.raises(ThemeConfigurationError):
        themes.load_theme('alt_theme')
