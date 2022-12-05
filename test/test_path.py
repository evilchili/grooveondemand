import pytest
import os

from groove import path
from groove.exceptions import ConfigurationError


def test_missing_theme_root(monkeypatch):
    broken_env = {k: v for (k, v) in os.environ.items()}
    broken_env['GROOVE_ON_DEMAND_ROOT'] = '/dev/null/missing'
    monkeypatch.setattr(os, 'environ', broken_env)
    with pytest.raises(ConfigurationError):
        path.themes_root()
