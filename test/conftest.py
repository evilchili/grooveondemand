import pytest

import groove.db

from sqlalchemy import create_engine, insert
from sqlalchemy.orm import sessionmaker


@pytest.fixture(scope='function')
def in_memory_engine():
    return create_engine('sqlite:///:memory:', future=True)


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
        {'id': 1, 'relpath': '/UNKLE/Psyence Fiction/01 Guns Blazing (Drums of Death, Part 1).flac'},
        {'id': 2, 'relpath': '/UNKLE/Psyence Fiction/02 UNKLE (Main Title Theme).flac'},
        {'id': 3, 'relpath': '/UNKLE/Psyence Fiction/03 Bloodstain.flac'}
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
