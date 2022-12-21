import pytest
import os

from pathlib import Path
from dotenv import load_dotenv

import groove.db
from groove.playlist import Playlist

from sqlalchemy import create_engine, insert
from sqlalchemy.orm import sessionmaker

from unittest.mock import MagicMock


@pytest.fixture(autouse=True, scope='function')
def env():
    root = Path(__file__).parent / Path('fixtures')
    load_dotenv(Path('test/fixtures/env'))
    os.environ['GROOVE_ON_DEMAND_ROOT'] = str(root)
    os.environ['MEDIA_ROOT'] = str(root / Path('media'))
    os.environ['DATABASE_PATH'] = ''
    return os.environ


@pytest.fixture(scope='function')
def auth():
    return (os.environ.get('USERNAME'), os.environ.get('PASSWORD'))


@pytest.fixture(scope='function')
def in_memory_engine(monkeypatch):
    engine = create_engine('sqlite:///:memory:', future=True)
    monkeypatch.setattr('groove.db.manager.create_engine',
                        MagicMock(return_value=engine))
    return engine


@pytest.fixture(scope='function')
def in_memory_db(in_memory_engine):
    """
    An (empty) in-memory SQLite3 database
    """
    Session = sessionmaker(bind=in_memory_engine, future=True)
    session = Session()
    groove.db.metadata.create_all(bind=in_memory_engine)
    yield session
    session.close()


@pytest.fixture(scope='function')
def db(in_memory_db):
    """
    Populate the in-memory sqlite database with fixture data.
    """

    # create tracks
    query = insert(groove.db.track)
    in_memory_db.execute(query, [
        {'id': 1, 'artist': 'UNKLE', 'title': 'Guns Blazing', 'relpath': 'UNKLE/Psyence Fiction/01 Guns Blazing (Drums of Death, Part 1).flac'},
        {'id': 2, 'artist': 'UNKLE', 'title': 'UNKLE', 'relpath': 'UNKLE/Psyence Fiction/02 UNKLE (Main Title Theme).flac'},
        {'id': 3, 'artist': 'UNKLE', 'title': 'Bloodstain', 'relpath': 'UNKLE/Psyence Fiction/03 Bloodstain.flac'}
    ])

    # create playlists
    query = insert(groove.db.playlist)
    in_memory_db.execute(query, [
        {'id': 1, 'name': 'playlist one', 'description': 'the first one', 'slug': 'playlist-one'},
        {'id': 2, 'name': 'playlist two', 'description': 'the second one', 'slug': 'playlist-two'},
        {'id': 3, 'name': 'playlist three', 'description': 'the threerd one', 'slug': 'playlist-three'},
        {'id': 4, 'name': 'empty playlist', 'description': 'no tracks', 'slug': 'empty-playlist'}
    ])

    # populate the playlists
    query = insert(groove.db.entry)
    in_memory_db.execute(query, [
        {'playlist_id': '1', 'track': '1', 'track_id': '1'},
        {'playlist_id': '1', 'track': '2', 'track_id': '2'},
        {'playlist_id': '1', 'track': '3', 'track_id': '3'},

        {'playlist_id': '2', 'track': '1', 'track_id': '1'},

        {'playlist_id': '3', 'track': '6', 'track_id': '2'},
        {'playlist_id': '3', 'track': '2', 'track_id': '3'},
    ])
    yield in_memory_db


@pytest.fixture(scope='function')
def empty_playlist(db):
    return Playlist.by_slug('empty-playlist', session=db)
