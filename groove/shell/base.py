import functools
from collections import namedtuple, defaultdict

from prompt_toolkit.completion import Completer, Completion
from groove.console import Console
from textwrap import dedent

COMMANDS = defaultdict(dict)

Command = namedtuple('Commmand', 'prompt,handler,usage')


def register_command(handler, usage):
    prompt = handler.__qualname__.split('.', -1)[0]
    cmd = handler.__name__
    if cmd not in COMMANDS[prompt]:
        COMMANDS[prompt][cmd] = Command(prompt=prompt, handler=handler, usage=usage)


def command(usage):
    def decorator(func):
        register_command(func, usage)

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)
        return wrapper
    return decorator


class BasePrompt(Completer):

    def __init__(self, manager=None, console=None, parent=None):
        super(BasePrompt, self).__init__()

        if (not manager and not parent):  # pragma: no cover
            raise RuntimeError("Must define either a database manager or a parent object.")

        self._prompt = ''
        self._autocomplete_values = []
        self._parent = parent
        self._manager = manager
        self._console = None
        self._theme = None

    def _get_help(self, cmd=None):
        try:
            return dedent(COMMANDS[self.__class__.__name__][cmd].usage)
        except KeyError:
            return self.usage

    def default_completer(self, document, complete_event):
        raise NotImplementedError(f"Implement the 'default_completer' method of {self.__class__.__name__}")

    @property
    def usage(self):
        text = dedent("""
        [title]GROOVE ON DEMAND INTERACTIVE SHELL[/title]

        Available commands are listed below. Try 'help COMMAND' for detailed help.

        [title]COMMANDS[/title]

        """)
        for (name, cmd) in sorted(self.commands.items()):
            text += f"    [b]{name:10s}[/b]    {cmd.handler.__doc__.strip()}\n"
        return text

    @property
    def commands(self):
        return COMMANDS[self.__class__.__name__]

    @property
    def console(self):
        if not self._console:
            self._console = Console(color_system='truecolor')
        return self._console

    @property
    def manager(self):
        if self._manager:
            return self._manager
        elif self._parent:
            return self._parent.manager

    @property
    def parent(self):
        return self._parent

    @property
    def prompt(self):
        return self._prompt

    @property
    def autocomplete_values(self):
        return self._autocomplete_values

    def get_completions(self, document, complete_event):
        word = document.get_word_before_cursor()
        found = False
        for value in self.autocomplete_values:
            if word in value:
                found = True
                yield Completion(value, start_position=-len(word))
        if not found:
            try:
                for result in self.default_completer(document, complete_event):
                    yield result
            except NotImplementedError:
                pass

    def help(self, parts):
        attr = None
        if parts:
            attr = parts[0]
        self.console.print(self._get_help(attr))
        return True

    def process(self, cmd, *parts):
        if cmd in self.commands:
            return self.commands[cmd].handler(self, parts)
        self.console.error(f"Command {cmd} not understood.")

    def start(self, cmd=''):
        while True:
            if not cmd:
                cmd = self.console.prompt(self.prompt, completer=self)
            if not cmd:
                return
            cmd, *parts = cmd.split()
            res = self.process(cmd, *parts)
            if res is False:
                return res
            cmd = ''
