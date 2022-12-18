import os

from configparser import ConfigParser
from pathlib import Path
from textwrap import dedent

from rich.console import Console as _Console
from rich.markdown import Markdown
from rich.theme import Theme
from rich.table import Table

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


def console_theme(theme_name=None):
    cfg = ConfigParser()
    cfg.read_dict({'styles': BASE_STYLE})
    cfg.read(theme(
        theme_name or os.environ['DEFAULT_THEME']) / Path('console.cfg')
    )
    return cfg['styles']


class Console(_Console):

    def __init__(self, *args, **kwargs):
        self._console_theme = console_theme(kwargs.get('theme', None))
        kwargs['theme'] = Theme(self._console_theme, inherit=False)
        super().__init__(*args, **kwargs)

    @property
    def theme(self):
        return self._console_theme

    def prompt(self, lines, **kwargs):
        for line in lines[:-1]:
            super().print(line)
        with self.capture() as capture:
            super().print(f"[prompt bold]{lines[-1]}>[/] ", end='')
        rendered = ANSI(capture.get())
        return _toolkit_prompt(rendered, **kwargs)

    def mdprint(self, txt, **kwargs):
        self.print(Markdown(dedent(txt), justify='left'), **kwargs)

    def print(self, txt, **kwargs):
        super().print(txt, **kwargs)

    def error(self, txt, **kwargs):
        super().print(dedent(txt), style='error')

    def table(self, *cols, **params):
        if os.environ['CONSOLE_THEMES']:
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
