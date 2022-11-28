from sqlalchemy import MetaData
from sqlalchemy import Table, Column, Integer, String, UnicodeText, ForeignKey, PrimaryKeyConstraint

metadata = MetaData()

track = Table(
    "track",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("relpath", UnicodeText, index=True, unique=True),
    Column("artist", UnicodeText),
    Column("title", UnicodeText),
)

playlist = Table(
    "playlist",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("name", String),
    Column("description", UnicodeText),
    Column("slug", String, index=True, unique=True),
)

entry = Table(
    "entry",
    metadata,
    Column("track", Integer),
    Column("playlist_id", Integer, ForeignKey("playlist.id")),
    Column("track_id", Integer, ForeignKey("track.id")),
    PrimaryKeyConstraint("playlist_id", "track"),
)
