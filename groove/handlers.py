from prompt_toolkit import prompt
from prompt_toolkit.completion import Completion, FuzzyCompleter
from slugify import slugify
from sqlalchemy import func
from rich import print

from groove import db
from groove.playlist import Playlist


class FuzzyTableCompleter(FuzzyCompleter):

    def __init__(self, table, column, formatter, session):
        super(FuzzyTableCompleter).__init__()
        self._table = table
        self._column = column
        self._formatter = formatter
        self._session = session

    def get_completions(self, document, complete_event):
        word = document.get_word_before_cursor()
        query = self._session.query(self._table).filter(self._column.ilike(f"%{word}%"))
        for row in query.all():
            yield Completion(
                self._formatter(row),
                start_position=-len(word)
            )


class Command:
    def __init__(self, processor):
        self._processor = processor

    def handle(self, *parts):
        raise NotImplementedError()


class help(Command):
    """Display the help documentation."""
    def handle(self, *parts):
        print("Available commands:")
        for handler in Command.__subclasses__():
            print(f"{handler.__name__}: {handler.__doc__}")


class add(Command):
    """Add a track to the current playlist."""
    def handle(self, *parts):
        if not self._processor.playlist:
            print("Please select a playlist first, using the 'playlist' command.")
            return
        text = prompt(
            'Add which track? > ',
            completer=FuzzyTableCompleter(db.track, db.track.c.relpath, self._track_to_string, self._processor.session),
            complete_in_thread=True, complete_while_typing=True
        )
        return text

    def _track_to_string(row):
        return f"{row.artist} - {row.title}"


class list(Command):
    """Display the current playlist."""
    def handle(self, *parts):
        if not self._processor.playlist:
            print("Please select a playlist first, using the 'playlist' command.")
            return
        print(self._processor.playlist.as_dict)


class stats(Command):
    """Display database statistics."""
    def handle(self, *parts):
        sess = self._processor.session
        playlists = sess.query(func.count(db.playlist.c.id)).scalar()
        entries = sess.query(func.count(db.entry.c.track)).scalar()
        tracks = sess.query(func.count(db.track.c.relpath)).scalar()
        print(f"Database contains {playlists} playlists with a total of {entries} entries, from {tracks} known tracks.")


class quit(Command):
    """Exit the interactive shell."""
    def handle(self, *parts):
        raise SystemExit()


class playlist(Command):
    """Create or load a playlist."""
    def handle(self, *parts):
        name = ' '.join(parts)
        slug = slugify(name)
        self._processor.playlist = Playlist(
            slug=slug,
            name=name,
            session=self._processor.session,
            create_if_not_exists=True
        )
        self._processor.prompt = slug
        print(f"Loaded playlist with slug {self._processor.playlist.record.slug}.")


def load(processor):
    for handler in Command.__subclasses__():
        yield handler.__name__, handler(processor)
