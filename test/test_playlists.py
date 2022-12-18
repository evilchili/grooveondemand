import pytest
import yaml

from unittest.mock import MagicMock

from groove import playlist, editor
from groove.exceptions import PlaylistValidationError, TrackNotFoundError

from yaml.scanner import ScannerError


def test_create(empty_playlist):
    assert empty_playlist.record.id


def test_get_no_create(in_memory_db):
    pl = playlist.Playlist(name='something', session=in_memory_db, create_ok=False)

    # assert twice to ensure we cache the first db query result.
    assert pl.get_or_create() is None
    assert pl.get_or_create() is None


def test_exists(db):
    pl = playlist.Playlist(name='something', session=db, create_ok=True)
    assert pl.exists


def test_exists_deleted(empty_playlist):
    assert empty_playlist.exists
    empty_playlist.delete()
    assert not empty_playlist.exists


@pytest.mark.parametrize('vals, expected', [
    (dict(slug='missing-the-name', name=''), PlaylistValidationError),
])
def test_create_missing_fields(vals, expected, db):
    with pytest.raises(expected):
        assert playlist.Playlist(**vals, session=db, create_ok=True).record.id


@pytest.mark.parametrize('tracks', [
    ('01 Guns Blazing', ),
    ('01 Guns Blazing', '02 UNKLE'),
])
def test_add(tracks, empty_playlist):
    assert empty_playlist.add(tracks) == len(tracks)


def test_add_no_matches(empty_playlist):
    with pytest.raises(TrackNotFoundError):
        empty_playlist.add(('no match', ))


def test_add_multiple_matches(empty_playlist):
    assert empty_playlist.add('UNKLE',) == 0


def test_delete(empty_playlist):
    expected = empty_playlist.record.id
    assert empty_playlist.delete() == expected
    assert not empty_playlist.exists
    assert empty_playlist.deleted


def test_delete_playlist_not_exist(db):
    pl = playlist.Playlist(name='foo', slug='foo', session=db, create_ok=False)
    assert not pl.delete()
    assert not pl.exists
    assert not pl.deleted


def test_cannot_create_after_delete(db, empty_playlist):
    empty_playlist.delete()
    with pytest.raises(PlaylistValidationError):
        assert empty_playlist.record
    assert not empty_playlist.exists


def test_entries(db):
    # assert twice for branch coverage of cached values
    pl = playlist.Playlist.by_slug('playlist-one', db)
    assert pl.entries
    assert pl.entries


def test_playlist_not_exist_formatted(db):
    pl = playlist.Playlist(name='foo', slug='foo', session=db, create_ok=False)
    assert repr(pl)
    assert pl.as_dict


def test_playlist_formatted(db, empty_playlist):
    assert repr(empty_playlist)
    assert empty_playlist.as_string
    assert empty_playlist.as_dict


def test_playlist_equality(db):
    pl = playlist.Playlist(name='foo', slug='foo', session=db, create_ok=False)
    pl2 = playlist.Playlist(name='foo', slug='foo', session=db, create_ok=False)
    assert pl == pl2
    pl.save()
    assert pl == pl2


def test_playlist_inequality(db):
    pl = playlist.Playlist(name='foo', slug='foo', session=db, create_ok=False)
    pl2 = playlist.Playlist(name='bar', slug='foo', session=db, create_ok=False)
    assert pl != pl2
    pl.save()
    assert pl != pl2


def test_playlist_inequality_tracks_differ(db):
    pl = playlist.Playlist.from_yaml({
        'foo': {
            'description': '',
            'entries': []
        }
    }, db)
    pl2 = playlist.Playlist.from_yaml({
        'foo': {
            'description': '',
            'entries': [
                {'UNKLE': 'Guns Blazing'},
            ]
        }
    }, db)
    assert pl != pl2


def test_as_yaml(db):
    expected = {
        'playlist one': {
            'description': 'the first one\n',
            'entries': [
                {'UNKLE': 'Guns Blazing'},
                {'UNKLE': 'UNKLE'},
                {'UNKLE': 'Bloodstain'},
            ]
        }
    }
    pl = playlist.Playlist.by_slug('playlist-one', db)
    assert yaml.safe_load(pl.as_yaml) == expected


def test_from_yaml(db):
    pl = playlist.Playlist.by_slug('playlist-one', db)
    pl2 = playlist.Playlist.from_yaml(yaml.safe_load(pl.as_yaml), db)
    assert pl2 == pl


@pytest.mark.parametrize('src', [
    {'missing description': {'entries': []}},
    {'missing entries': {'description': 'foo'}},
    {'empty': {}},
    {'': {'description': 'no name', 'entries': []}},
])
def test_from_yaml_missing_values(src, db):
    with pytest.raises(PlaylistValidationError):
        playlist.Playlist.from_yaml(src, db)


@pytest.mark.parametrize('edits, expected', [
    ({'edited': {'description': 'the edited one', 'entries': []}}, 'edited'),
    ({'empty playlist': {'description': 'no tracks', 'entries': []}}, 'empty playlist'),
    (None, 'empty playlist'),
])
def test_edit(monkeypatch, edits, expected, empty_playlist):
    monkeypatch.setattr(
        empty_playlist._editor, 'edit', MagicMock(spec=editor, return_value=edits)
    )
    empty_playlist.edit()
    assert empty_playlist.name == expected


@pytest.mark.parametrize('error', [TypeError, ScannerError, TrackNotFoundError])
def test_edit_errors(monkeypatch, error, empty_playlist):
    monkeypatch.setattr('groove.playlist.Playlist.from_yaml', MagicMock(
        side_effect=error
    ))
    with pytest.raises(PlaylistValidationError):
        empty_playlist.edit()


@pytest.mark.parametrize('error', [IOError, OSError, FileNotFoundError])
def test_edit_errors_in_editor(monkeypatch, error, empty_playlist):
    monkeypatch.setattr('groove.editor.subprocess.check_call', MagicMock(
        side_effect=error
    ))
    with pytest.raises(RuntimeError):
        empty_playlist.edit()


def test_edit_yaml_error_in_editor(monkeypatch, empty_playlist):
    monkeypatch.setattr('groove.editor.PlaylistEditor.read', MagicMock(
        side_effect=ScannerError
    ))
    with pytest.raises(PlaylistValidationError):
        empty_playlist.edit()


@pytest.mark.parametrize('slug', [None, ''])
def test_save_no_slug(slug, empty_playlist):
    empty_playlist._slug = slug
    with pytest.raises(PlaylistValidationError):
        empty_playlist.save()@pytest.mark.parametrize('slug', [None, ''])


@pytest.mark.parametrize('name', [None, ''])
def test_save_no_name(name, empty_playlist):
    empty_playlist._name = name
    with pytest.raises(PlaylistValidationError):
        empty_playlist.save()
