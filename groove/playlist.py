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
                 create_ok=True):
        self._session = session
        self._slug = slug
        self._name = name
        self._description = description
        self._entries = None
        self._record = None
        self._create_ok = create_ok
        self._deleted = False

    @property
    def deleted(self) -> bool:
        return self._deleted

    @property
    def exists(self) -> bool:
        if self.deleted:
            logging.debug("Playlist has been deleted.")
            return False
        if not self._record:
            if self._create_ok:
                return True and self.record
            return False
        return True

    @property
    def summary(self):
        return ' :: '.join([
            f"[ {self.record.id} ]",
            self.record.name,
            f"http://{os.environ['HOST']}/{self.slug}",
        ])

    @property
    def slug(self) -> str:
        return self._slug

    @property
    def session(self) -> Session:
        return self._session

    @property
    def record(self) -> Union[Row, None]:
        """
        Cache the playlist row from the database and return it. Optionally create it if it doesn't exist.
        """
        if not self._record:
            self._record = self.get_or_create()
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
            self._entries = query.all()
        return self._entries

    @property
    def as_dict(self) -> dict:
        """
        Return a dictionary of the playlist and its entries.
        """
        if not self.exists:
            return {}
        playlist = dict(self.record)
        playlist['entries'] = [dict(entry) for entry in self.entries]
        return playlist

    @property
    def as_string(self) -> str:
        if not self.exists:
            return ''
        text = f"{self.summary}\n"
        for entry in self.entries:
            text += f"  - {entry.track}  {entry.artist} - {entry.title}\n"
        return text

    def _get_tracks_by_path(self, paths: List[str]) -> List:
        """
        Retrieve tracks from the database that match the specified path fragments. The exceptions NoResultFound and
        MultipleResultsFound are expected in the case of no matches and multiple matches, respectively.
        """
        return [self.session.query(db.track).filter(db.track.c.relpath.ilike(f"%{path}%")).one() for path in paths]

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
        self._deleted = True
        return plid

    def get_or_create(self, create_ok: bool = False) -> Row:
        try:
            return self.session.query(db.playlist).filter(db.playlist.c.slug == self.slug).one()
        except NoResultFound:
            logging.debug(f"Could not find a playlist with slug {self.slug}.")
        if self.deleted:
            raise RuntimeError("Object has been deleted.")
        if self._create_ok or create_ok:
            return self.save()

    def load(self):
        self.get_or_create(create_ok=False)
        return self

    def save(self) -> Row:
        keys = {'slug': self.slug, 'name': self._name, 'description': self._description}
        stmt = db.playlist.update(keys) if self._record else db.playlist.insert(keys)
        results = self.session.execute(stmt)
        self.session.commit()
        logging.debug(f"Saved playlist {results.inserted_primary_key[0]} with slug {self.slug}")
        return self.session.query(db.playlist).filter(db.playlist.c.id == results.inserted_primary_key[0]).one()

    def create_entries(self, tracks: List[Row]) -> int:
        """
        Append a list of tracks to a playlist by populating the entries table with records referencing the playlist and
        the specified tracks.

        Args:
            tracks (list): A list of Row objects from the track table.

        Returns:
            int: The number of tracks added.
        """
        maxtrack = self.session.query(func.max(db.entry.c.track)).filter_by(
            playlist_id=self.record.id
        ).one()[0] or 0

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

    @classmethod
    def from_row(cls, row, session):
        pl = Playlist(slug=row.slug, session=session)
        pl._record = row
        return pl

    def __repr__(self):
        return self.as_string
