import logging
import os
from collections import namedtuple
from pathlib import Path

from groove.exceptions import ThemeConfigurationError, ConfigurationError

import groove.path


Theme = namedtuple('Theme', 'name,path,author,author_link,version,about')


def load_theme(name=None):
    name = name or os.environ.get('DEFAULT_THEME', None)
    if not name:  # pragma: no cover
        raise ConfigurationError(
            "It seems like DEFAULT_THEME is not set in your current environment.\n"
            "Running 'groove setup' may help you fix this problem."
        )
    theme_path = groove.path.theme(name)
    theme_info = _get_theme_info(theme_path)
    try:
        return Theme(
            name=name,
            path=theme_path,
            **theme_info
        )
    except TypeError:
        raise ThemeConfigurationError(f"The {name} them is misconfigured. Does the README.md contain a credits secton?")


def _get_theme_info(theme_path):
    readme = theme_path / Path('README.md')
    if not readme.exists:  # pragma: no cover
        raise ThemeConfigurationError(
            "The theme is missing a required file: README.md.\n"
            "Refer to the Groove On Demand documentation for help creating themes."
        )
    config = {
        'about': '',
    }
    with readme.open() as fh:
        in_credits = False
        in_block = False
        for line in fh.readlines():
            line = line.strip()
            if line == '## Credits':
                in_credits = True
                continue
            config['about'] += line
            if not in_credits:
                continue
            if line == '```':
                if not in_block:
                    in_block = True
                    continue
                break
            try:
                (key, value) = line.split(':', 1)
                key = key.strip()
                value = value.strip()
            except ValueError:
                logging.warning(f"Could not parse credits line: {line}")
                continue
            logging.debug(f"Setting theme '{key}' to '{value}'.")
            config[key] = value
    return config
