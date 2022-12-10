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

    def default_completer(self, document, complete_event):  # pragma: no cover
        def _formatter(row):
            self._playlist = Playlist.from_row(row, self.manager.session)
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
            return True
        self._playlist = Playlist(
            slug=slugify(name),
            name=name,
            session=self.manager.session,
            create_ok=True
        )
        self.commands['_playlist'].start()
        return True


def start():  # pragma: no cover
    with database_manager() as manager:
        CommandPrompt(manager).start()
