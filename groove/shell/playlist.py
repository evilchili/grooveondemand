from .base import BasePrompt

import os

from sqlalchemy.exc import NoResultFound
from textwrap import dedent, wrap
from rich.table import Column
from rich import box

from groove import db
from groove.exceptions import PlaylistValidationError


class _playlist(BasePrompt):
    """
    """

    def __init__(self, parent, manager=None):
        super().__init__(manager=manager, parent=parent)
        self._parent = parent
        self._commands = None

    @property
    def help_text(self):
        synopsis = (
            f"You are currently editing the [b]{self.parent.playlist.name}[/b]"
            f" playlist. From this prompt you can quickly append new tracks "
            f"to the playlist. You can invoke your editor "
            f"([link]{os.environ['EDITOR']}[/link]) to change the playlist "
            f"name and description, or reorder or remove tracks. You can also "
            f"delete the playlist."
        )

        try:
            width = int(os.environ.get('CONSOLE_WIDTH', '80'))
        except ValueError:
            width = 80
        synopsis = '\n        '.join(wrap(synopsis, width=width))

        return dedent(f"""
        [title]WORKING WITH PLAYLISTS[/title]

        {synopsis}

        [title]USAGE[/title]

            [link]playlist> COMMAND [ARG ..][/link]

        [title]COMMANDS[/title]
        [help]
            [b]add[/b]      Add one or more tracks to the playlist
            [b]edit[/b]     Open the playlist in the system editor
            [b]show[/b]     Display the complete playlist
            [b]delete[/b]   Delete the playlist
            [b]help[/b]     This message

            Try 'help command' for command-specific help.[/help]
        """)

    @property
    def prompt(self):
        return [
            "",
            "[help]Available commands: add, edit, show, delete, help. Hit Enter to return.[/help]",
            f"[prompt]{self.parent.playlist.slug}[/prompt]",
        ]

    @property
    def values(self):
        return self.commands.keys()

    @property
    def commands(self):
        if not self._commands:
            self._commands = {
                'delete': self.delete,
                'add': self.add,
                'show': self.show,
                'edit': self.edit,
                'help': self.help
            }
        return self._commands

    def process(self, cmd, *parts):
        if cmd in self.commands:
            return True if self.commands[cmd](parts) else False
        self.parent.console.error(f"Command not understood: {cmd}")
        return True

    def edit(self, *parts):
        try:
            self.parent.playlist.edit()
        except PlaylistValidationError as e:
            self.parent.console.error(f"Changes were not saved: {e}")
        else:
            self.show()
        return True

    def show(self, *parts):
        pl = self.parent.playlist
        title = f"\n [b]:headphones: {pl.name}[/b]"
        if pl.description:
            title += f"\n [italic]{pl.description}[/italic]\n"
        table = self.parent.console.table(
            Column('#', justify='right', width=4),
            Column('Artist', justify='left'),
            Column('Title', justify='left'),
            box=box.HORIZONTALS,
            title=title,
            title_justify='left',
            caption=f"[link]{pl.url}[/link]",
            caption_justify='right',
        )
        for (num, entry) in enumerate(pl.entries):
            table.add_row(
                f"[text]{num+1}[/text]",
                f"[artist]{entry.artist}[/artist]",
                f"[title]{entry.title}[/title]"
            )
        self.parent.console.print(table)
        return True

    def add(self, *parts):
        self.parent.console.print(
            "Add tracks one at a time by title. Hit Enter to finish."
        )
        added = False
        while True:
            text = self.parent.console.prompt(
                [' ?'],
                completer=self.manager.fuzzy_table_completer(
                    db.track,
                    db.track.c.relpath,
                    lambda row: row.relpath
                ),
                complete_in_thread=True, complete_while_typing=True
            )
            if not text:
                if added:
                    self.show()
                return True
            self._add_track(text)
            added = True

    def _add_track(self, text):
        sess = self.parent.manager.session
        try:
            track = sess.query(db.track).filter(db.track.c.relpath == text).one()
            self.parent.playlist.create_entries([track])
        except NoResultFound:
            self.parent.console.error("No match for '{text}'")
            return
        return text

    def delete(self, *parts):
        res = self.parent.console.prompt([
            f"[error]Type [b]DELETE[/b] to permanently delete the playlist "
            f'"{self.parent.playlist.record.name}".[/error]',
            f"[prompt]DELETE {self.parent.playlist.slug}[/prompt]",
        ])
        if res != 'DELETE':
            self.parent.console.error("Delete aborted. No changes have been made.")
            return True

        self.parent.playlist.delete()
        self.parent.console.print("Deleted the playlist.")
        self.parent._playlist = None
        return False

    def start(self):
        self.show()
        super().start()
