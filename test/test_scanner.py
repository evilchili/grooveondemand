import pytest
import os
from pathlib import Path
from unittest.mock import MagicMock
from sqlalchemy import func

import groove.exceptions
from groove.media import scanner
from groove.db import track


def test_scanner(monkeypatch, in_memory_db):

    def mock_loader(path):
        return {
            'artist': 'foo',
            'title': 'bar',
        }
    monkeypatch.setattr(scanner.MediaScanner, '_get_tags', MagicMock(side_effect=mock_loader))
    test_scanner = scanner.MediaScanner(path=Path('UNKLE'), db=in_memory_db)

    # verify all entries are scanned
    assert test_scanner.scan() == 1

    # readback; verify entries are in the db
    query = func.count(track.c.relpath)
    query = query.filter(track.c.relpath.ilike('%UNKLE%'))
    assert in_memory_db.query(query).scalar() == 1

    # verify idempotency
    assert test_scanner.scan() == 0


def test_scanner_no_media_root(in_memory_db):
    del os.environ['MEDIA_ROOT']
    with pytest.raises(groove.exceptions.ConfigurationError):
        assert scanner.MediaScanner(path=None, db=in_memory_db)
