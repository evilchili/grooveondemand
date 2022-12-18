import logging
import os

from textwrap import indent
from typing import Union, List

from groove import db
from groove.editor import PlaylistEditor, EDITOR_TEMPLATE
from groove.exceptions import PlaylistValidationError, TrackNotFoundError

from slugify import slugify
from sqlalchemy import func, delete
from sqlalchemy.orm.session import Session
from sqlalchemy.engine.row import Row
from sqlalchemy.exc import NoResultFound, MultipleResultsFound

from yaml.scanner import ScannerError


class Playlist:
    """
    CRUD operations and convenience methods for playlists.
    """
    def __init__(self,
                 name: str,
                 session: Session,
                 slug: str = '',
                 description: str = '',
                 create_ok=True):
        self._session = session
        self._name = name
        if not self._name:
            raise PlaylistValidationError("Name cannot be empty.")
        self._slug = slug or slugify(name)
        self._description = description
        self._entries = []
        self._record = None
        self._create_ok = create_ok
        self._deleted = False
        self._editor = PlaylistEditor()

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
    def editor(self):
        return self._editor

    @property
    def name(self):
        return self._name

    @property
    def description(self):
        return self._description

    @property
    def info(self):
        count = len(self.entries)
        return f"{self.name}: {self.url} [{count} tracks]\n{self.description}\n"

    @property
    def url(self) -> str:
        return f"http://{os.environ['HOST']}:{os.environ['PORT']}/{self.slug}"

    @property
    def slug(self) -> str:
        return self._slug

    @property
    def session(self) -> Session:
        return self._session

    @property
    def record(self) -> Union[Row, None, bool]:
        """
        Cache the playlist row from the database and return it. Optionally create it if it doesn't exist.

        Returns:
            None:   If we've never tried to get or create the record
            False:  False if we've tried and failed to get the record
            Row:    The record as it appears in the database.
        """
        if self._record is None:
            self.get_or_create()
        return self._record

    @property
    def entries(self) -> List:
        """
        Cache the list of entries on this playlist and return it.
        """
        if not self._entries:
            if self.record:
                query = self.session.query(
                    db.entry,
                    db.track
                ).filter(
                    (db.playlist.c.id == self._record.id)
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
        playlist = {
            'name': self.name,
            'slug': self.slug,
            'description': self.description
        }
        if self.record:
            playlist.update(dict(self.record))
        playlist['entries'] = [dict(entry) for entry in self.entries]
        return playlist

    @property
    def as_string(self) -> str:
        text = self.info
        for (tracknum, entry) in enumerate(self.entries):
            text += f"  {tracknum+1:-3d}.  {entry.artist} - {entry.title}\n"
        return text

    @property
    def as_yaml(self) -> str:
        template_vars = self.as_dict
        template_vars['description'] = indent(template_vars['description'], prefix='    ')
        template_vars['entries'] = ''
        for entry in self.entries:
            template_vars['entries'] += f'  - "{entry.artist}": "{entry.title}"\n'
        return EDITOR_TEMPLATE.format(**template_vars)

    def _get_tracks_by_path(self, paths: List[str]) -> List:
        """
        Retrieve tracks from the database that match the specified path fragments. The exceptions NoResultFound and
        MultipleResultsFound are expected in the case of no matches and multiple matches, respectively.
        """
        for path in paths:
            try:
                yield self.session.query(db.track).filter(
                    db.track.c.relpath.ilike(f"%{path}%")
                ).one()
            except NoResultFound:
                raise TrackNotFoundError(f'Could not find track for path "{path}"')

    def _get_tracks_by_artist_and_title(self, entries: List[tuple]) -> List:
        for (artist, title) in entries:
            try:
                yield self.session.query(db.track).filter(
                    db.track.c.artist == artist, db.track.c.title == title
                ).one()
            except NoResultFound:  # pragma: no cover
                raise TrackNotFoundError(f'Could not find track "{artist}": "{title}"')

    def _get(self):
        try:
            return self.session.query(db.playlist).filter(
                db.playlist.c.slug == self.slug
            ).one()
        except NoResultFound:
            logging.debug(f"Could not find a playlist with slug {self.slug}.")
        return False

    def _insert(self, values):
        stmt = db.playlist.insert(values)
        results = self.session.execute(stmt)
        self.session.commit()
        logging.debug(f"Inserted playlist with slug {self.slug}")
        return self.session.query(db.playlist).filter(
            db.playlist.c.id == results.inserted_primary_key[0]
        ).one()

    def _update(self, values):
        stmt = db.playlist.update().where(
            db.playlist.c.id == self._record.id
        ).values(values)
        self.session.execute(stmt)
        self.session.commit()
        return self.session.query(db.playlist).filter(
            db.playlist.c.id == self._record.id
        ).one()

    def edit(self):
        edits = self.editor.edit(self)
        if not edits:
            return
        try:
            new = Playlist.from_yaml(edits, self.session)
            if new == self:
                logging.debug("No changes detected.")
                return
        except (TypeError, ScannerError) as e:
            logging.error(e)
            raise PlaylistValidationError(
                "An error occurred reading the input file; this is typically "
                "the result of an error in the YAML structure."
            )
        except TrackNotFoundError as e:
            logging.error(e)
            raise PlaylistValidationError(
                "One or more of the specified tracks "
                "did not exactly match an entry in the database."
            )
        logging.debug(f"Updating {self.slug} with new edits.")
        self._slug = new.slug
        self._name = new.name.strip()
        self._description = new.description.strip()
        self._entries = new._entries
        self.save()

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
            return self.create_entries(list(self._get_tracks_by_path(paths)))
        except NoResultFound:  # pragma: no cover
            logging.error("One or more of the specified paths do not match any tracks in the database.")
            return 0
        except MultipleResultsFound:  # pragma: no cover
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
        if self._record is None:
            self._record = self._get()
            if self._record:
                self._description = self._record.description
                self._name = self._record.name
                self._slug = self._record.slug
        if not self._record:
            if self.deleted:
                raise PlaylistValidationError("Object has been deleted.")
            if self._create_ok or create_ok:
                self.save()

    def save(self) -> Row:
        values = {
            'slug': self.slug,
            'name': self.name,
            'description': self.description
        }
        if not self.name:
            raise PlaylistValidationError("This playlist has no name.")
        if not self.slug:
            raise PlaylistValidationError("This playlist has no slug.")
        self._record = self._update(values) if self._record else self._insert(values)
        logging.debug(f"Saved playlist {self._record.id} with slug {self._record.slug}")
        self.save_entries()

    def save_entries(self):
        plid = self.record.id
        stmt = delete(db.entry).where(db.entry.c.playlist_id == plid)
        logging.debug(f"Deleting stale entries associated with playlist {plid}: {stmt}")
        self.session.execute(stmt)
        return self.create_entries(self.entries)

    def create_entries(self, tracks: List[Row]) -> int:
        """
        Append a list of tracks to a playlist by populating the entries table with records referencing the playlist and
        the specified tracks.

        Args:
            tracks (list): A list of Row objects from the track table.

        Returns:
            int: The number of tracks added.
        """
        if not tracks:
            tracks = self.entries
        if not tracks:
            return 0
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
    def by_slug(cls, slug, session):
        try:
            row = session.query(db.playlist).filter(
                db.playlist.c.slug == slug
            ).one()
        except NoResultFound as ex:
            logging.error(f"Could not locate an existing playlist with slug {slug}.")
            raise ex
        return cls.from_row(row, session)

    @classmethod
    def from_row(cls, row, session):
        pl = Playlist(
            slug=row.slug,
            name=row.name,
            description=row.description,
            session=session
        )
        pl._record = row
        return pl

    @classmethod
    def from_yaml(cls, source, session, create_ok=False):
        try:
            name = list(source.keys())[0].strip()
            description = (source[name]['description'] or '').strip()
            pl = Playlist(
                slug=slugify(name),
                name=name,
                description=description,
                session=session,
                create_ok=create_ok
            )
            if not source[name]['entries']:
                pl._entries = []
            else:
                pl._entries = list(pl._get_tracks_by_artist_and_title(entries=[
                    list(entry.items())[0] for entry in source[name]['entries']
                ]))
        except (IndexError, KeyError, AttributeError):
            raise PlaylistValidationError("The specified source was not a valid playlist.")
        return pl

    def __eq__(self, obj):
        logging.debug(f"Comparing obj to self:\n{obj.as_string}\n--\n{self.as_string}")
        return obj.as_string == self.as_string
        for key in ('slug', 'name', 'description'):
            if getattr(obj, key) != getattr(self, key):
                logging.debug(f"{key}: {getattr(obj, key)} != {getattr(self, key)}")
                return False
        return True

    def __repr__(self):
        return self.as_string
