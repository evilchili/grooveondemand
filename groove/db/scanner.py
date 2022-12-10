import asyncio
import logging
import os
import music_tag

from pathlib import Path
from typing import Callable, Union, Iterable
from sqlalchemy import func, delete

import groove.db
import groove.path


class MediaScanner:
    """
    Scan a directory structure containing audio files and import them into the database.
    """
    def __init__(self, root: Union[Path, None], db: Callable, glob: Union[str, None] = None) -> None:
        self._db = db
        self._glob = tuple((glob or os.environ.get('MEDIA_GLOB')).split(','))
        self._root = root or groove.path.media_root()
        logging.debug(f"Configured media scanner for root: {self._root}")

    @property
    def db(self) -> Callable:
        return self._db

    @property
    def root(self) -> Path:
        return self._root

    @property
    def glob(self) -> tuple:
        return self._glob

    def find_sources(self, pattern):
        return self.root.rglob(pattern)  # pragma: no cover

    def import_tracks(self, sources: Iterable) -> None:
        async def _do_import():
            logging.debug("Scanning filesystem (this may take a minute)...")
            for path in sources:
                if path.exists() and not path.is_dir():
                    asyncio.create_task(self._import_one_track(path))
        asyncio.run(_do_import())
        self.db.commit()

    def cleanup(self) -> int:
        """
        Check for the existence of every track in the databse.
        """
        async def _del(track):
            path = self.root / Path(track.relpath)
            if path.exists():
                return
            logging.info(f"Deleting missing track {track.relpath}")
            self.db.execute(
                delete(groove.db.track).where(groove.db.track.c.id == track.id)
            )

        async def _do_cleanup():
            logging.debug("Locating stale track definitions in the database...")
            for track in self.db.query(groove.db.track).all():
                asyncio.create_task(_del(track))
        asyncio.run(_do_cleanup())
        self.db.commit()

    def _get_tags(self, path):  # pragma: no cover
        tags = music_tag.load_file(path)
        return {
            'artist': str(tags.resolve('album_artist')),
            'title': str(tags['title']),
        }

    async def _import_one_track(self, path):
        tags = self._get_tags(path)
        tags['relpath'] = str(path.relative_to(self.root))
        stmt = groove.db.track.insert(tags).prefix_with('OR IGNORE')
        logging.debug(f"{tags['artist']} - {tags['title']}")
        self.db.execute(stmt)

    def scan(self) -> int:
        """
        Walk the media root and insert Track table entries for each media file
        found. Existing entries will be ignored.
        """
        count = self.db.query(func.count(groove.db.track.c.relpath)).scalar()
        logging.debug(f"Track table currently contains {count} entries.")
        for pattern in self.glob:
            self.import_tracks(self.find_sources(pattern))
            newcount = self.db.query(func.count(groove.db.track.c.relpath)).scalar() - count
            logging.debug(f"Inserted {newcount} new tracks so far this run...")
        return newcount


media_scanner = MediaScanner
