import os

from configparser import ConfigParser
from pathlib import Path
from textwrap import dedent
from typing import Union, List

import rich.repr

from rich.console import Console as _Console
from rich.markdown import Markdown
from rich.theme import Theme
from rich.table import Table, Column

from prompt_toolkit import prompt as _toolkit_prompt
from prompt_toolkit.formatted_text import ANSI

from groove.path import theme

BASE_STYLE = {
    'help': 'cyan',
    'bright': 'white',
    'repr.str': 'dim',
    'repr.brace': 'dim',
    'repr.url': 'blue',
}


def console_theme(theme_name: Union[str, None] = None) -> dict:
    """
    Return a console theme as a dictionary.

    Args:
        theme_name (str):
    """
    cfg = ConfigParser()
    cfg.read_dict({'styles': BASE_STYLE})
    cfg.read(theme(
        theme_name or os.environ['DEFAULT_THEME']) / Path('console.cfg')
    )
    return cfg['styles']


@rich.repr.auto
class Console(_Console):
    """
    SYNOPSIS

        Subclasses a rich.console.Console to provide an instance with a
        reconfigured themes, and convenience methods and attributes.

    USAGE

        Console([ARGS])

    ARGS

        theme       The name of a theme to load. Defaults to DEFAULT_THEME.

    EXAMPLES

        Console().print("Can I kick it?")
        >>> Can I kick it?

    INSTANCE ATTRIBUTES

        theme       The current theme

    """

    def __init__(self, *args, **kwargs):
        self._console_theme = console_theme(kwargs.get('theme', None))
        self._overflow = 'ellipsis'
        kwargs['theme'] = Theme(self._console_theme, inherit=False)
        super().__init__(*args, **kwargs)

    @property
    def theme(self) -> Theme:
        return self._console_theme

    def prompt(self, lines: List, **kwargs) -> str:
        """
        Print a list of lines, using the final line as a prompt.

        Example:

            Console().prompt(["Can I kick it?", "[Y/n] ")
            >>> Can I kick it?
            [Y/n]>

        """
        for line in lines[:-1]:
            super().print(line)
        with self.capture() as capture:
            super().print(f"[prompt bold]{lines[-1]}>[/] ", end='')
        rendered = ANSI(capture.get())
        return _toolkit_prompt(rendered, **kwargs)

    def mdprint(self, txt: str, **kwargs) -> None:
        """
        Like print(), but support markdown. Text will be dedented.
        """
        self.print(Markdown(dedent(txt), justify='left'), **kwargs)

    def print(self, txt: str, **kwargs) -> None:
        """
        Print text to the console, possibly truncated with an ellipsis.
        """
        super().print(txt, overflow=self._overflow, **kwargs)

    def error(self, txt: str, **kwargs) -> None:
        """
        Print text to the console with the current theme's error style applied.
        """
        self.print(dedent(txt), style='error')

    def table(self, *cols: List[Column], **params) -> None:
        """
        Print a rich table to the console with theme elements and styles applied.
        parameters and keyword arguments are passed to rich.table.Table.
        """
        background_style = f"on {self.theme['background']}"
        params.update(
            header_style=background_style,
            title_style=background_style,
            border_style=background_style,
            row_styles=[background_style],
            caption_style=background_style,
            style=background_style,
        )
        params['min_width'] = 80
        width = os.environ.get('CONSOLE_WIDTH', 'auto')
        if width == 'expand':
            params['expand'] = True
        elif width != 'auto':
            params['width'] = int(width)
        return Table(*cols, **params)
