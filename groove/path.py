import logging
import os

from pathlib import Path
from groove.exceptions import ConfigurationError, ThemeMissingException, ThemeConfigurationError

_setup_hint = "You may be able to solve this error by running 'groove setup' or specifying the --root parameter."
_reinstall_hint = "You might need to reinstall Groove On Demand to fix this error."


def root():
    path = Path(__file__).parent.expanduser().absolute() / Path('static')
    logging.debug(f"Root is {path}")
    return Path(path)


def media_root():
    path = os.environ.get('MEDIA_ROOT', None)
    if not path:
        raise ConfigurationError(f"MEDIA_ROOT is not defined in your environment.\n\n{_setup_hint}")
    path = Path(path).expanduser()
    if not path.exists() or not path.is_dir():
        raise ConfigurationError(
            "The media_root directory (MEDIA_ROOT) doesn't exist, or isn't a directory.\n\n{_setup_hint}"
        )
    logging.debug(f"Media root is {path}")
    return path


def cache_root():
    path = os.environ.get('CACHE_ROOT', None)
    if not path:
        raise ConfigurationError(f"CACHE_ROOT is not defined in your environment.\n\n{_setup_hint}")
    path = Path(path).expanduser()
    logging.debug(f"Media cache root is {path}")
    return path


def media(relpath):
    path = media_root() / Path(relpath)
    return path


def transcoded_media(relpath):
    path = cache_root() / Path(relpath + '.webm')
    return path


def static_root():
    dirname = os.environ.get('STATIC_PATH', 'static')
    path = root() / Path(dirname)
    logging.debug(f"Static root is {path}")
    if not path.exists() or not path.is_dir():
        raise ConfigurationError(  # pragma: no cover
            f"The static assets directory {dirname} (STATIC_PATH) "
            f"doesn't exist, or isn't a directory.\n\n{_reinstall_hint}"
        )
    return path


def static(relpath, theme=None):
    if theme:
        root = theme.path / Path('static')
        if not root.is_dir():
            raise ThemeConfigurationError(  # pragma: no cover
                f"The themes directory {relpath} (THEMES_PATH) "
                f"doesn't contain a 'static' directory."
            )
        path = root / Path(relpath)
        logging.debug(f"Checking for {path}")
        if path.exists():
            return path
    path = static_root() / Path(relpath)
    logging.debug(f"Defaulting to {path}")
    return path


def themes_root():
    dirname = os.environ.get('THEMES_PATH', 'themes')
    path = root() / Path(dirname)
    if not path.exists() or not path.is_dir():
        raise ConfigurationError(  # pragma: no cover
            f"The themes directory {dirname} (THEMES_PATH) "
            f"doesn't exist, or isn't a directory.\n\n{_reinstall_hint}"
        )
    logging.debug(f"Themes root is {path}")
    return path


def theme(name):
    path = themes_root() / Path(name)
    if not path.exists():
        available = ','.join(available_themes())
        raise ThemeMissingException(
            f"A theme directory named {name} does not exist or isn't a directory. "
            "Perhaps there is a typo in the name?\n"
            f"Available themes: {available}"
        )
    return path


def theme_template(template_name):
    return Path('templates') / Path(f"{template_name}.tpl")


def available_themes():
    return [theme.name for theme in themes_root().iterdir() if theme.is_dir()]


def database():
    path = Path(os.environ.get('DATABASE_PATH', '~')).expanduser()
    if not path.exists() or not path.is_dir():
        raise ConfigurationError(
            "DATABASE_PATH doesn't exist or isn't a directory.\n\n{_setup_hint}"
        )
    return path / Path('groove_on_demand.db')
