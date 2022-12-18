from .base import BasePrompt, command

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
        self._console = parent.console

    @property
    def usage(self):
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
        except ValueError:  # pragma: no cover
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

            Try 'help COMMAND' for command-specific help.[/help]
        """)

    @property
    def prompt(self):
        return [
            "",
            "[help]Available commands: add, edit, show, delete, help. Hit Enter to return.[/help]",
            f"[prompt]{self.parent.playlist.slug}[/prompt]",
        ]

    def start(self):
        self.show()
        super().start()

    @command("""
    [title]EDITING A PLAYLIST[/title]

    Use the [b]edit[/b] commmand to edit a YAML-formatted versin of the playlist
    in your external editor as specified by the $EDITOR environment variable.

    You can use this feature to rename a playlist, change its description, and
    delete or reorder the playlist's entries. Save and exit the file when you
    are finished editing, and the playlist will be updated with your changes.

    To abort the edit session, exit your editor without saving the file.

    [title]USAGE[/title]

        [link]playlist> edit[/link]
    """)
    def edit(self, *parts):
        try:
            self.parent.playlist.edit()
        except PlaylistValidationError as e:  # pragma: no cover
            self.console.error(f"Changes were not saved: {e}")
        else:
            self.show()
        return True

    @command("""
    [title]VIEWS FOR THE VIEWMASTER[/title]

    Use the [b]show[/b] command to display the contents of the current playlist.

    [title]USAGE[/title]

        [link]playlist> show[/link]
    """)
    def show(self, *parts):
        pl = self.parent.playlist
        title = f"\n [b]:headphones: {pl.name}[/b]"
        if pl.description:
            title += f"\n [italic]{pl.description}[/italic]\n"
        table = self.console.table(
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
        self.console.print(table)
        return True

    @command("""
    [title]ADDING TRACKS TO A PLAYLIST[/title]

    Use the [b]add[/b] command to interactively add one or more tracks from
    your media sources to the current playlist. At the prompt, start typing the
    name of an artist, album, or song title; matches from the file names in
    your library will be suggested automatically. To accept a match, hit <TAB>,
    or use the arrow keys to choose a different suggestion.

    Hit <ENTER> to add your selected track to the current playlist. You can
    then add another track, or hit <ENTER> again to return to the playlist
    editor.

    [title]USAGE[/title]

        [link]playlist> add[/link]
        [link] ?> PATHNAME
    """)
    def add(self, *parts):
        self.console.print(
            "Add tracks one at a time by title. Hit Enter to finish."
        )
        added = False
        while True:
            text = self.console.prompt(
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
        except NoResultFound:  # pragma: no cover
            self.console.error("No match for '{text}'")
            return
        return text

    @command("""
    [title]DELETING A PLAYLIST[/title]
    Use the [b]delete[/b] command to delete the current playlist. You will be
    prompted to type DELETE, to ensure you really mean it. If you
    enter anything other than DELETE, the delete request will
    be aborted.

    [danger]Deleting a playlist cannot be undone![/danger]

    [title]USAGE[/title]

        [link]playlist> delete[/link]
        Type DELETE to permanently delete the playlist.
        [link]DELETE playlist> DELETE
    """)
    def delete(self, parts):
        res = self.console.prompt([
            f"[error]Type [b]DELETE[/b] to permanently delete the playlist "
            f'"{self.parent.playlist.record.name}".[/error]',
            f"[prompt]DELETE {self.parent.playlist.slug}[/prompt]",
        ])
        if res != 'DELETE':
            self.console.error("Delete aborted. No changes have been made.")
            return True

        self.parent.playlist.delete()
        self.console.print("Deleted the playlist.")
        self.parent._playlist = None
        return False

    @command("""
    [title]HELP![/title]

    The [b]help[/b] command will print usage information for whatever you're currently
    doing. You can also ask for help on any command currently available.

    [title]USAGE[/title]

        [link]> help [COMMAND][/link]
    """)
    def help(self, parts):
        super().help(parts)
