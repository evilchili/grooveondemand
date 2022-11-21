import logging
import os
import sys

from pathlib import Path
from typing import Callable, Union, Iterable
from sqlalchemy import func

import groove.db


class MediaScanner:
    """
    Scan a directory structure containing audio files and import them into the database.
    """
    def __init__(self, root: Path, db: Callable, glob: Union[str, None] = None) -> None:
        self._db = db
        self._glob = tuple((glob or os.environ.get('MEDIA_GLOB')).split(','))
        try:
            self._root = root or Path(os.environ.get('MEDIA_ROOT'))
        except TypeError:
            logging.error("Could not find media root. Do you need to define MEDIA_ROOT in your environment?")
            sys.exit(1)
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
        return self.root.rglob(pattern)  # pragma: no-cover

    def import_tracks(self, sources: Iterable) -> None:
        for path in sources:
            relpath = str(path.relative_to(self.root))
            stmt = groove.db.track.insert({'relpath': relpath}).prefix_with('OR IGNORE')
            self.db.execute(stmt)
        self.db.commit()

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
