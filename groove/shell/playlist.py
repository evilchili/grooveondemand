from .base import BasePrompt

from prompt_toolkit import prompt
from rich import print
from sqlalchemy.exc import NoResultFound

from groove import db


class _playlist(BasePrompt):

    def __init__(self, parent, manager=None):
        super().__init__(manager=manager, parent=parent)
        self._parent = parent
        self._prompt = ''
        self._commands = None

    @property
    def prompt(self):
        return f"{self.parent.playlist}\n{self.parent.playlist.slug}> "

    @property
    def values(self):
        return self.commands.keys()

    @property
    def commands(self):
        if not self._commands:
            self._commands = {
                'show':  self.show,
                'delete': self.delete,
                'add': self.add,
                'edit': self.edit,
            }
        return self._commands

    def process(self, cmd, *parts):
        if cmd in self.commands:
            return True if self.commands[cmd](parts) else False
        print(f"Command not understood: {cmd}")
        return True

    def show(self, parts):
        print(self.parent.playlist)
        return True

    def edit(self, parts):
        self.parent.playlist.edit()
        return True

    def add(self, parts):
        print("Add tracks one at a time by title. ENTER to finish.")
        while True:
            text = prompt(
                '  ?',
                completer=self.manager.fuzzy_table_completer(
                    db.track,
                    db.track.c.relpath,
                    lambda row: row.relpath
                ),
                complete_in_thread=True, complete_while_typing=True
            )
            if not text:
                return True
            self._add_track(text)

    def _add_track(self, text):
        sess = self.parent.manager.session
        try:
            track = sess.query(db.track).filter(db.track.c.relpath == text).one()
            self.parent.playlist.create_entries([track])
        except NoResultFound:
            print("No match for '{text}'")
            return
        return text

    def delete(self, parts):
        res = prompt(
            'Type DELETE to permanently delete the playlist '
            f'"{self.parent.playlist.record.name}".\nDELETE {self.prompt}'
        )
        if res != 'DELETE':
            print("Delete aborted. No changes have been made.")
            return True

        self.parent.playlist.delete()
        print("Deleted the playlist.")
        self.parent._playlist = None
        return False
