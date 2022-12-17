import os

from pathlib import Path
from textwrap import dedent

from rich.console import Console as _Console
from rich.markdown import Markdown
from rich.theme import Theme

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


class Console(_Console):

    def __init__(self, *args, **kwargs):
        if 'theme' not in kwargs:
            theme_path = theme(os.environ['DEFAULT_THEME'])
            kwargs['theme'] = Theme(BASE_STYLE).read(theme_path / Path('console.cfg'), inherit=False)
        super().__init__(*args, **kwargs)

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
