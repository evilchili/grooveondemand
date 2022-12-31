from slugify import slugify

from groove.db.manager import database_manager
from groove.media.scanner import MediaScanner
from groove.shell.base import BasePrompt, command
from groove.exceptions import InvalidPathError
from groove import db
from groove.playlist import Playlist

from rich.table import Column
from rich import box

from sqlalchemy import func


class InteractiveShell(BasePrompt):

    def __init__(self, manager):
        super().__init__(manager=manager)
        self._playlist = None
        self._completer = None
        self._prompt = [
            "[help]Groove on Demand interactive shell. Try 'help' for help.[/help]",
            "groove"
        ]
        self._subshells = {}
        self._register_subshells()

    def _register_subshells(self):
        for subclass in BasePrompt.__subclasses__():
            if subclass.__name__ == self.__class__.__name__:
                continue
            self._subshells[subclass.__name__] = subclass(manager=self.manager, parent=self)

    def _get_stats(self):
        playlists = self.manager.session.query(func.count(db.playlist.c.id)).scalar()
        entries = self.manager.session.query(func.count(db.entry.c.track)).scalar()
        tracks = self.manager.session.query(func.count(db.track.c.relpath)).scalar()
        return f"Database contains {playlists} playlists with a total of {entries} entries, from {tracks} known tracks."

    @property
    def playlist(self):
        return self._playlist

    @property
    def autocomplete_values(self):
        return list(self.commands.keys())

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
        if cmd in self.commands:
            return self.commands[cmd].handler(self, parts)
        name = cmd + ' ' + ' '.join(parts)
        self.load([name.strip()])

    @command("""
    [title]SCANNING YOUR MEDIA[/title]

    Use the [b]scan[/b] function to scan your media root for new, changed, and
    deleted audio files. This process may take some time if you have a large
    library!

    Instead of scanning the entire MEDIA_ROOT, you can specify a PATH, which
    must be a subdirectory of your MEDIA_ROOT. This is useful to import that
    new new.

    [title]USAGE[/title]

        [link]> scan [PATH][/link]

    """)
    def scan(self, parts):
        """
        Scan your MEDIA_ROOT for changes.
        """
        path = ' '.join(parts) if parts else None
        try:
            scanner = MediaScanner(path=path, db=self.manager.session, console=self.console)
        except InvalidPathError as e:
            self.console.error(str(e))
            return True
        scanner.scan()

    @command("""
    [title]LISTS FOR THE LIST LOVER[/title]

    The [b]list[/b] command will display a summary of all playlists currently stored
    in the Groove on Demand database.

    [title]USAGE[/title]

        [link]> list[/link]

    """)
    def list(self, parts):
        """
        List all playlists.
        """
        table = self.console.table(
            Column('#', justify='right', width=4),
            Column('Name'),
            Column('Tracks', justify='right', width=4),
            Column('Description'),
            Column('Link'),
            box=box.HORIZONTALS,
            title=' :headphones: Groove on Demand Playlists',
            title_justify='left',
            caption=self._get_stats(),
            caption_justify='right',
            expand=True
        )
        query = self.manager.session.query(db.playlist)
        for row in db.windowed_query(query, db.playlist.c.id, 1000):
            pl = Playlist.from_row(row, self.manager.session)
            table.add_row(
                f"[dim]{pl.record.id}[/dim]",
                f"[title]{pl.record.name}[/title]",
                f"[text]{len(pl.entries)}[/text]",
                f"[text]{pl.record.description}[/text]",
                f"[link]{pl.url}[/link]",
            )
        self.console.print(table)
        return True

    @command(usage="""
    [title]LOADING PLAYLISTS[/title]

    Use the [b]load[/b] command to load an existing playlist from the database
    and start the playlist editor. If the specified playlist does not exist,
    it will be created automatically.

    Matching playlist names will be suggested as you type; hit <TAB> to accept
    the current suggestion, or use the arrow keys to choose a different
    suggestion.

    [title]USAGE[/title]

        [link]> load NAME[/link]

    """)
    def load(self, parts):
        """
        Load the named playlist and create it if it does not exist.
        """
        name = ' '.join(parts)
        if not name:
            return
        slug = slugify(name)
        self._playlist = Playlist(
            slug=slug,
            name=name,
            session=self.manager.session,
            create_ok=True
        )
        self._subshells['_playlist'].start()
        return True

    @command(usage="""
    [title]DATABASE STATISTICS[/title]

    The [b]stats[/b] command displays interesting statistics about the database.

    [title]USAGE[/title]

        [link]> stats[/link]
    """)
    def stats(self, parts):
        """
        Display database statistics.
        """
        self.console.print(self._get_stats())

    @command(usage="""
    [title]HIT IT AND QUIT IT[/title]

    The [b]quit[/b] command exits the Groove on Demand interactive shell.

    [title]USAGE[/title]

        [link]> quit|^D|<ENTER>[/link]
    """)
    def quit(self, parts):
        """
        Quit Groove on Demand.
        """
        raise SystemExit('Find the 1.')

    @command(usage="""
    [title]HELP FOR THE HELP LORD[/title]

    The [b]help[/b] command will print usage information for whatever you're currently
    doing. You can also ask for help on any command currently available.

    [title]USAGE[/title]

        [link]> help [COMMAND][/link]
    """)
    def help(self, parts):
        """
        Display the help message.
        """
        super().help(parts)
        return True


def start():  # pragma: no cover
    with database_manager() as manager:
        InteractiveShell(manager).start()
