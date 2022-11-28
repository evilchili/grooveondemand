from prompt_toolkit import prompt
from prompt_toolkit.completion import Completer, Completion
from rich import print

from groove import db
from groove import handlers
from groove.db.manager import database_manager
from groove.playlist import Playlist


class CommandProcessor(Completer):

    prompt = ''

    def __init__(self, session):
        super(CommandProcessor, self).__init__()
        self._session = session
        self.playlist = None
        self._handlers = dict(handlers.load(self))
        print(f"Loaded command handlers: {' '.join(self._handlers.keys())}")

    @property
    def session(self):
        return self._session

    def get_completions(self, document, complete_event):
        word = document.get_word_before_cursor()
        found = False
        for command_name in self._handlers.keys():
            if word in command_name:
                yield Completion(command_name, start_position=-len(word))
                found = True
        if not found:
            def _formatter(row):
                self.playlist = Playlist.from_row(row, self._session)
                return f'playlist {self.playlist.record.name}'
            completer = handlers.FuzzyTableCompleter(
                db.playlist,
                db.playlist.c.name,
                _formatter,
                self._session
            )
            for res in completer.get_completions(document, complete_event):
                yield res

    def process(self, cmd):
        if not cmd:
            return
        cmd, *parts = cmd.split()
        if cmd in self._handlers:
            self._handlers[cmd].handle(*parts)

    def start(self):
        cmd = ''
        while True:
            cmd = prompt(f'{self.prompt} > ', completer=self)
            self.process(cmd)
            if not cmd:
                self.cmd_exit()


def start_shell():
    print("Groove On Demand interactive shell.")
    with database_manager() as manager:
        CommandProcessor(manager.session).start()
