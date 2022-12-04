import os

from pathlib import Path
from groove.exceptions import ConfigurationError, ThemeMissingException

_setup_hint = "You may be able to solve this error by running 'groove setup'."
_reinstall_hint = "You might need to reinstall Groove On Demand to fix this error."


def root():
    path = os.environ.get('GROOVE_ON_DEMAND_ROOT', None)
    if not path:
        raise ConfigurationError(f"GROOVE_ON_DEMAND_ROOT is not defined in your environment.\n\n{_setup_hint}")
    path = Path(path).expanduser()
    if not path.exists or not path.is_dir:
        raise ConfigurationError(
            "The Groove on Demand root directory (GROOVE_ON_DEMAND_ROOT) "
            f"does not exist or isn't a directory.\n\n{_reinstall_hint}"
        )
    return Path(path)


def media_root():
    path = os.environ.get('MEDIA_ROOT', None)
    if not path:
        raise ConfigurationError(f"MEDIA_ROOT is not defined in your environment.\n\n{_setup_hint}")
    path =Path(path).expanduser()
    if not path.exists and path.is_dir:
        raise ConfigurationError(
            "The media_root directory (MEDIA_ROOT) doesn't exist, or isn't a directory.\n\n{_setup_hint}"
        )
    return path


def media(relpath):
    return themes_root() / Path(relpath)


def static_root():
    dirname = os.environ.get('STATIC_PATH', 'static')
    path = root() / Path(dirname)
    if not path.exists or not path.is_dir:
        raise ConfigurationError(
            f"The static assets directory {dirname} (STATIC_PATH) "
            f"doesn't exist, or isn't a directory.\n\n{_reinstall_hint}"
        )
    return path


def static(relpath):
    return static_root() / Path(relpath)


def themes_root():
    dirname = os.environ.get('THEMES_PATH', 'themes')
    path = root() / Path(dirname)
    if not path.exists or not path.is_dir:
        raise ConfigurationError(
            f"The themes directory {dirname} (THEMES_PATH) "
            f"doesn't exist, or isn't a directory.\n\n{_reinstall_hint}"
        )
    return path


def theme(name):
    path = themes_root() / Path(name)
    if not path.exists or not path.is_dir:
        available = ','.join(available_themes)
        raise ThemeMissingException(
            f"A theme directory named {name} does not exist or isn't a directory. "
            "Perhaps there is a typo in the name?\n"
            f"Available themes: {available}"
        )
    return path


def theme_static(relpath):
    return Path('static') / Path(relpath)


def theme_template(template_name):
    return Path('templates') / Path(f"{template_name}.tpl")


def available_themes():
    return [theme.name for theme in themes_root().iterdir() if theme.is_dir()]


def database():
    return root() / Path(os.environ.get('DATABASE_PATH', 'groove_on_demand.db'))
