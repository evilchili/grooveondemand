from rich import print
from slugify import slugify

from groove.db.manager import database_manager
from groove.shell.base import BasePrompt
from groove import db
from groove.playlist import Playlist


class CommandPrompt(BasePrompt):

    def __init__(self, manager):
        super().__init__(manager=manager)
        self._playlist = None
        self._prompt = "Groove on Demand interactive shell. Try 'help' for help.\ngroove>"
        self._completer = None
        self._commands = None

    @property
    def playlist(self):
        return self._playlist

    @property
    def commands(self):
        if not self._commands:
            self._commands = {}
            for cmd in BasePrompt.__subclasses__():
                if cmd.__name__ == self.__class__.__name__:
                    continue
                self._commands[cmd.__name__] = cmd(manager=self.manager, parent=self)
        return self._commands

    @property
    def values(self):
        return [k for k in self.commands.keys() if not k.startswith('_')]

    def default_completer(self, document, complete_event):
        def _formatter(row):
            self._playlist = Playlist.from_row(row, self.manager)
            return self.playlist.record.name
        return self.manager.fuzzy_table_completer(
            db.playlist,
            db.playlist.c.name,
            _formatter
         ).get_completions(document, complete_event)

    def process(self, cmd, *parts):
        name = cmd + ' ' + ' '.join(parts)
        if cmd in self.commands:
            self.commands[cmd].start(name)
        elif not parts:
            print(f"Command not understood: {cmd}")
        else:
            slug = slugify(name)
            self._playlist = Playlist(
                slug=slug,
                name=name,
                session=self.manager.session,
                create_if_not_exists=False
            )
            self.commands['_playlist'].start()
            self._playlist = None
        return True


def start():
    with database_manager() as manager:
        CommandPrompt(manager).start()
