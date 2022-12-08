import pytest
from groove import playlist
from groove.exceptions import PlaylistValidationError


def test_create(empty_playlist):
    assert empty_playlist.record.id


@pytest.mark.parametrize('vals, expected', [
    (dict(name='missing-the-slug', ), TypeError),
    (dict(name='missing-the-slug', slug=''), PlaylistValidationError),
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
    assert empty_playlist.add(('no match', )) == 0


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
    with pytest.raises(RuntimeError):
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
