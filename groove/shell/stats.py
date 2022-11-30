from .base import BasePrompt

from sqlalchemy import func
from rich import print

from groove import db


class stats(BasePrompt):

    def process(self, cmd, *parts):
        sess = self.parent.manager.session
        playlists = sess.query(func.count(db.playlist.c.id)).scalar()
        entries = sess.query(func.count(db.entry.c.track)).scalar()
        tracks = sess.query(func.count(db.track.c.relpath)).scalar()
        print(f"Database contains {playlists} playlists with a total of {entries} entries, from {tracks} known tracks.")
