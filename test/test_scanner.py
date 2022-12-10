import pytest
import os
from pathlib import Path
from unittest.mock import MagicMock
from sqlalchemy import func

import groove.exceptions
from groove.db import scanner, track


fixture_tracks = [
    "/test/Spookey Ruben/Modes of Transportation, Volume 1/Spookey Ruben - Modes of Transportation, Volume 1 - 01 Terra Magnifica.flac",
    "/test/Spookey Ruben/Modes of Transportation, Volume 1/Spookey Ruben - Modes of Transportation, Volume 1 - 02 These Days Are Old.flac",
    "/test/Spookey Ruben/Modes of Transportation, Volume 1/Spookey Ruben - Modes of Transportation, Volume 1 - 03 Crystal Cradle.flac",
    "/test/Spookey Ruben/Modes of Transportation, Volume 1/Spookey Ruben - Modes of Transportation, Volume 1 - 04 Running Away.flac",
    "/test/Spookey Ruben/Modes of Transportation, Volume 1/Spookey Ruben - Modes of Transportation, Volume 1 - 05 Welcome to the House of Food.flac",
    "/test/Spookey Ruben/Modes of Transportation, Volume 1/Spookey Ruben - Modes of Transportation, Volume 1 - 06 Wendy McDonald.flac",
    "/test/Spookey Ruben/Modes of Transportation, Volume 1/Spookey Ruben - Modes of Transportation, Volume 1 - 07 The Size of You.flac",
    "/test/Spookey Ruben/Modes of Transportation, Volume 1/Spookey Ruben - Modes of Transportation, Volume 1 - 08 Its Not What You Do Its You.flac",
    "/test/Spookey Ruben/Modes of Transportation, Volume 1/Spookey Ruben - Modes of Transportation, Volume 1 - 09 Mars.flac",
    "/test/Spookey Ruben/Modes of Transportation, Volume 1/Spookey Ruben - Modes of Transportation, Volume 1 - 10 Leave the City.flac",
    "/test/Spookey Ruben/Modes of Transportation, Volume 1/Spookey Ruben - Modes of Transportation, Volume 1 - 11 Growing Up is Over.flac",
    "/test/Spookey Ruben/Modes of Transportation, Volume 1/Spookey Ruben - Modes of Transportation, Volume 1 - 12 Donate Your Heart to a Stranger....flac",
    "/test/Spookey Ruben/Modes of Transportation, Volume 1/Spookey Ruben - Modes of Transportation, Volume 1 - 13 Life Insurance.flac",
]


@pytest.fixture
def media():
    def fixture():
        for t in fixture_tracks:
            yield Path(t)
    return fixture


def test_scanner(monkeypatch, in_memory_db, media):

    # replace the filesystem glob with the test fixture generator
    monkeypatch.setattr(scanner.MediaScanner, 'find_sources', MagicMock(return_value=media()))

    def mock_loader(path):
        return {
            'artist': 'foo',
            'title': 'bar',
        }

    # replace music_tag so it doesn't try to read things
    monkeypatch.setattr(scanner.MediaScanner, '_get_tags', MagicMock(side_effect=mock_loader))

    test_scanner = scanner.media_scanner(root=Path('/test'), db=in_memory_db)
    expected = len(fixture_tracks)

    # verify all entries are scanned
    assert test_scanner.scan() == expected

    # readback; verify entries are in the db
    query = func.count(track.c.relpath)
    query = query.filter(track.c.relpath.ilike('%Spookey%'))
    assert in_memory_db.query(query).scalar() == expected

    # verify idempotency
    assert test_scanner.scan() == 0


def test_scanner_no_media_root(in_memory_db):
    del os.environ['MEDIA_ROOT']
    with pytest.raises(groove.exceptions.ConfigurationError):
        assert scanner.media_scanner(root=None, db=in_memory_db)
