import asyncio
import logging
import os

from itertools import chain
from pathlib import Path
from typing import Callable, Union, Iterable

import music_tag
import rich.repr

from rich.console import Console
from rich.progress import (
    Progress,
    TextColumn,
    BarColumn,
    SpinnerColumn,
    TimeRemainingColumn
)
from sqlalchemy import func
from sqlalchemy.exc import NoResultFound

import groove.db
import groove.path

from groove.exceptions import InvalidPathError


@rich.repr.auto(angular=True)
class MediaScanner:
    """
    SYNOPSIS

        Scan a directory structure containing audio files and import track entries
        into the Groove on Demand database. Existing tracks will be ignored.

    USAGE

        MediaScanner(db=DB, [ARGS])

    ARGS

        db          An sqlalchemy databse session
        console     A rich console instance
        glob        A pattern to search for. Defaults to MEDIA_GLOB.  Multiple
                    patterns can be specifed as a comma-separated-list.
        path        The path to scan. Defaults to MEDIA_ROOT.
        root        The media root, as specified by MEDIA_ROOT

    EXAMPLES

        MediaScanner(db=DB, path='Kid Koala', glob='*.mp3').scan()
        >>> 15

    INSTANCE ATTRIBUTES

        db          The databse session
        console     The rich console instance
        glob        The globs to search for
        path        The path to be scanned
        root        The media root

    """
    def __init__(
        self,
        db: Callable,
        path: Union[Path, None] = None,
        glob: Union[str, None] = None,
        console: Union[Console, None] = None,
    ) -> None:
        self._db = db
        self._glob = tuple((glob or os.environ.get('MEDIA_GLOB', '*.mp3,*.flac,*.m4a')).split(','))
        self._root = groove.path.media_root()
        self._console = console or Console()
        self._scanned = 0
        self._imported = 0
        self._total = 0
        self._path = self._configure_path(path)

    @property
    def db(self) -> Callable:
        return self._db

    @property
    def console(self) -> Console:
        return self._console

    @property
    def root(self) -> Path:
        return self._root

    @property
    def path(self) -> Path:
        return self._path

    @property
    def glob(self) -> tuple:
        return self._glob

    def _configure_path(self, path):
        if not path:  # pragma: no cover
            return self._root
        fullpath = Path(self._root) / Path(path)
        if not (fullpath.exists() and fullpath.is_dir()):
            raise InvalidPathError(  # pragma: no cover
                f"[b]{fullpath}[/b] does not exist or is not a directory."
            )
        return fullpath

    def _get_tags(self, path):  # pragma: no cover
        tags = music_tag.load_file(path)
        return {
            'artist': str(tags.resolve('album_artist')),
            'title': str(tags['title']),
        }

    def find_sources(self, pattern):
        """
        Recursively search the instance path for files matching the pattern.
        """
        entrypoint = self._path if self._path else self._root
        for path in entrypoint.rglob(pattern):  # pragma: no cover
            if not path.is_dir():
                yield path

    def import_tracks(self, sources: Iterable) -> None:
        """
        Step through the specified source files and schedule async tasks to
        import them, reporting progress via a rich progress bar.
        """

        async def _do_import(progress, scanner):
            tasks = set()
            for path in sources:
                self._total += 1
                progress.update(scanner, total=self._total)
                tasks.add(asyncio.create_task(
                    self._import_one_track(path, progress, scanner)))
            progress.start_task(scanner)

        progress = Progress(
            TimeRemainingColumn(compact=True, elapsed_when_finished=True),
            BarColumn(bar_width=15),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%", justify="left"),
            TextColumn("[dim]|"),
            TextColumn("[title]{task.total:-6d}[/title] [b]total", justify="right"),
            TextColumn("[dim]|"),
            TextColumn("[title]{task.fields[imported]:-6d}[/title] [b]new", justify="right"),
            TextColumn("[dim]|"),
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console,
        )
        with progress:
            scanner = progress.add_task(
                f"[bright]Scanning [link]{self.path}[/link] (this may take some time)...",
                imported=0,
                total=0,
                start=False
            )
            asyncio.run(_do_import(progress, scanner))
            progress.update(
                scanner,
                completed=self._total,
                description=f"[bright]Scan of [link]{self.path}[/link] complete!",
            )

    async def _import_one_track(self, path, progress, scanner):
        """
        Import a single audo file into the databse, unless it already exists.
        """
        self._scanned += 1
        relpath = str(path.relative_to(self.root))
        try:
            self.db.query(groove.db.track).filter(
                groove.db.track.c.relpath == relpath).one()
            return
        except NoResultFound:
            pass

        columns = self._get_tags(path)
        columns['relpath'] = relpath

        logging.debug(f"Importing: {columns}")
        self.db.execute(groove.db.track.insert(columns))
        self.db.commit()
        self._imported += 1
        progress.update(
            scanner,
            imported=self._imported,
            completed=self._scanned,
            description=f"[bright]Imported [artist]{columns['artist']}[/artist]: [title]{columns['title']}[/title]",
        )

    def scan(self) -> int:
        """
        Walk the media root and insert Track table entries for each media file
        found. Existing entries will be ignored.
        """
        count = self.db.query(func.count(groove.db.track.c.relpath)).scalar()
        combined_sources = chain.from_iterable(
            self.find_sources(pattern) for pattern in self.glob
        )
        self.import_tracks(combined_sources)
        newcount = self.db.query(func.count(groove.db.track.c.relpath)).scalar() - count
        return newcount
