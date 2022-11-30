from groove import db
from sqlalchemy import func, delete
from sqlalchemy.orm.session import Session
from sqlalchemy.engine.row import Row
from sqlalchemy.exc import NoResultFound, MultipleResultsFound
from typing import Union, List

import logging
import os


class Playlist:
    """
    CRUD operations and convenience methods for playlists.
    """
    def __init__(self,
                 slug: str,
                 session: Session,
                 name: str = '',
                 description: str = '',
                 create_if_not_exists: bool = False):
        self._session = session
        self._slug = slug
        self._name = name
        self._description = description
        self._record = None
        self._entries = None
        self._create_if_not_exists = create_if_not_exists

    @property
    def exists(self) -> bool:
        """
        True if the playlist exists in the database.
        """
        return self.record is not None

    @property
    def summary(self):
        return ' :: '.join([
            f"[ {self.record.id} ]",
            self.record.name,
            f"http://{os.environ['HOST']}/{self.slug}",
        ])

    @property
    def slug(self) -> Union[str, None]:
        return self._slug

    @property
    def session(self) -> Union[Session, None]:
        return self._session

    @property
    def record(self) -> Union[Row, None]:
        """
        Cache the playlist row from the database and return it. Optionally create it if it doesn't exist.
        """
        if not self._record:
            try:
                self._record = self.session.query(db.playlist).filter(db.playlist.c.slug == self.slug).one()
                logging.debug(f"Retrieved playlist {self._record.id}")
            except NoResultFound:
                logging.debug(f"Could not find a playlist with slug {self.slug}.")
                pass
            if not self._record and self._create_if_not_exists:
                self._record = self._create()
                if not self._record:  # pragma: no cover
                    raise RuntimeError(f"Tried to create a playlist but couldn't read it back using slug {self.slug}")
        return self._record

    @property
    def entries(self) -> Union[List, None]:
        """
        Cache the list of entries on this playlist and return it.
        """
        if self.record and not self._entries:
            query = self.session.query(
                db.entry,
                db.track
            ).filter(
                (db.playlist.c.id == self.record.id)
            ).filter(
                db.entry.c.playlist_id == db.playlist.c.id
            ).filter(
                db.entry.c.track_id == db.track.c.id
            ).order_by(
                db.entry.c.track
            )
            # self._entries = list(db.windowed_query(query, db.entry.c.track_id, 1000))
            self._entries = query.all()
        return self._entries

    @property
    def as_dict(self) -> dict:
        """
        Return a dictionary of the playlist and its entries.
        """
        if not self.record:
            return {}
        playlist = dict(self.record)
        playlist['entries'] = [dict(entry) for entry in self.entries]
        return playlist

    @property
    def as_string(self) -> str:
        text = f"{self.summary}\n"
        for entry in self.entries:
            text += f"  - {entry.track}  {entry.artist} - {entry.title}\n"
        return text

    def add(self, paths: List[str]) -> int:
        """
        Add entries to the playlist.  Each path should match one and only one track in the database (case-insensitive).
        If a path doesn't match any track, or if a path matches multiple tracks, nothing is added to the playlist.

        Args:
            paths (list): A list of partial paths to add.

        Returns:
            int: The number of tracks added.
        """
        logging.debug(f"Attempting to add tracks matching: {paths}")
        try:
            return self.create_entries(self._get_tracks_by_path(paths))
        except NoResultFound:
            logging.error("One or more of the specified paths do not match any tracks in the database.")
            return 0
        except MultipleResultsFound:
            logging.error("One or more of the specified paths matches multiple tracks in the database.")
            return 0

    def delete(self) -> Union[int, None]:
        """
        Delete a playlist and its entries from the database, then clear the cached values.
        """
        if not self.record:
            return None
        plid = self.record.id
        stmt = delete(db.entry).where(db.entry.c.playlist_id == plid)
        logging.debug(f"Deleting entries associated with playlist {plid}: {stmt}")
        self.session.execute(stmt)
        stmt = delete(db.playlist).where(db.playlist.c.id == plid)
        logging.debug(f"Deleting playlist {plid}: {stmt}")
        self.session.execute(stmt)
        self.session.commit()
        self._record = None
        self._entries = None
        return plid

    def _get_tracks_by_path(self, paths: List[str]) -> List:
        """
        Retrieve tracks from the database that match the specified path fragments. The exceptions NoResultFound and
        MultipleResultsFound are expected in the case of no matches and multiple matches, respectively.
        """
        return [self.session.query(db.track).filter(db.track.c.relpath.ilike(f"%{path}%")).one() for path in paths]

    def create_entries(self, tracks: List[Row]) -> int:
        """
        Append a list of tracks to a playlist by populating the entries table with records referencing the playlist and
        the specified tracks.

        Args:
            tracks (list): A list of Row objects from the track table.

        Returns:
            int: The number of tracks added.
        """
        maxtrack = self.session.query(func.max(db.entry.c.track)).filter_by(playlist_id=self.record.id).one()[0] or 0
        self.session.execute(
            db.entry.insert(),
            [
                {'playlist_id': self.record.id, 'track_id': obj.id, 'track': idx}
                for (idx, obj) in enumerate(tracks, start=maxtrack+1)
            ]
        )
        self.session.commit()
        self._entries = None
        return len(tracks)

    def _create(self) -> Row:
        """
        Insert a new playlist record into the database.
        """
        stmt = db.playlist.insert({'slug': self.slug, 'name': self._name, 'description': self._description})
        results = self.session.execute(stmt)
        self.session.commit()
        logging.debug(f"Created new playlist {results.inserted_primary_key[0]} with slug {self.slug}")
        return self.session.query(db.playlist).filter(db.playlist.c.id == results.inserted_primary_key[0]).one()

    @classmethod
    def from_row(cls, row, session):
        pl = Playlist(slug=row.slug, session=session)
        pl._record = row
        return pl

    def __repr__(self):
        return self.as_string
