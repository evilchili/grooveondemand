from .base import BasePrompt

from rich.table import Table, Column
from rich import print

from sqlalchemy import func
from groove import db
from groove.playlist import Playlist


class browse(BasePrompt):
    """Browse the playlists."""

    def process(self, cmd, *parts):
        count = self.parent.manager.session.query(func.count(db.playlist.c.id)).scalar()
        print(f"Displaying {count} playlists:")
        query = self.parent.manager.session.query(db.playlist)
        table = Table(
            *[Column(k.name.title()) for k in db.playlist.columns]
        )
        for row in db.windowed_query(query, db.playlist.c.id, 1000):
            columns = tuple(Playlist.from_row(row, self.manager.session).record)[0:-1]
            table.add_row(*[str(col) for col in columns])
        print()
        print(table)
        print()
