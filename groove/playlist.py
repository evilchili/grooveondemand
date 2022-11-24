from groove import db
from sqlalchemy import func, delete
from sqlalchemy.exc import NoResultFound
import logging


class Playlist:
    """
    CRUD operations and convenience methods for playlists.
    """
    def __init__(self, slug, connection, create_if_not_exists=False):
        self._conn = connection
        self._slug = slug
        self._record = None
        self._entries = None
        self._create_if_not_exists = create_if_not_exists

    @property
    def exists(self):
        return self.record is not None

    @property
    def slug(self):
        return self._slug

    @property
    def conn(self):
        return self._conn

    @property
    def record(self):
        if not self._record:
            try:
                self._record = self.conn.query(db.playlist).filter(db.playlist.c.slug == self.slug).one()
                logging.debug(f"Retrieved playlist {self._record.id}")
            except NoResultFound:
                pass
            if self._create_if_not_exists:
                self._record = self._create()
                if not self._record:
                    raise RuntimeError(f"Tried to create a playlist but couldn't read it back using slug {self.slug}")
        return self._record

    @property
    def entries(self):
        if not self._entries:
            self._entries = self.conn.query(
                db.entry,
                db.track
            ).filter(
                (db.playlist.c.id == self.record.id)
            ).filter(
                db.entry.c.playlist_id == db.playlist.c.id
            ).filter(
                db.entry.c.track_id == db.track.c.id
            ).all()
        return self._entries

    @property
    def as_dict(self) -> dict:
        """
        Retrieve a playlist and its entries by its slug.
        """
        playlist = {}
        playlist = dict(self.record)
        playlist['entries'] = [dict(entry) for entry in self.entries]
        return playlist

    def add(self, paths) -> int:
        return self._create_entries(self._get_tracks_by_path(paths))

    def delete(self):
        plid = self.record.id
        stmt = delete(db.entry).where(db.entry.c.playlist_id == plid)
        logging.debug(f"Deleting entries associated with playlist {plid}: {stmt}")
        self.conn.execute(stmt)
        stmt = delete(db.playlist).where(db.playlist.c.id == plid)
        logging.debug(f"Deleting playlist {plid}: {stmt}")
        self.conn.execute(stmt)
        self.conn.commit()
        return plid

    def _get_tracks_by_path(self, paths):
        return [self.conn.query(db.track).filter(db.track.c.relpath.ilike(f"%{path}%")).one() for path in paths]

    def _create_entries(self, tracks):

        maxtrack = self.conn.query(func.max(db.entry.c.track)).filter_by(playlist_id=self.record.id).one()[0]
        self.conn.execute(
            db.entry.insert(),
            [
                {'playlist_id': self.record.id, 'track_id': obj.id, 'track': idx}
                for (idx, obj) in enumerate(tracks, start=maxtrack+1)
            ]
        )
        self.conn.commit()
        return len(tracks)

    def _create(self):
        stmt = db.playlist.insert({'slug': self.slug})
        results = self.conn.execute(stmt)
        self.conn.commit()
        logging.debug(f"Created new playlist {results.inserted_primary_key} with slug {self.slug}")
        return self.conn.query(db.playlist).filter(db.playlist.c.id == results.inserted_primary_key).one()
