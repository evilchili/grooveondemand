# 70, 73-81, 84, 88-97, 100-104
import pytest
from groove import playlist


def test_create(db):
    pl = playlist.Playlist(slug='test-create-playlist', session=db, create_ok=True)
    assert pl.record.id


@pytest.mark.parametrize('tracks', [
    ('01 Guns Blazing', ),
    ('01 Guns Blazing', '02 UNKLE'),
])
def test_add(db, tracks):
    pl = playlist.Playlist(slug='test-create-playlist', session=db)
    count = pl.add(tracks)
    assert count == len(tracks)


def test_add_no_matches(db):
    pl = playlist.Playlist(slug='playlist-one', session=db)
    assert pl.add(('no match', )) == 0


def test_add_multiple_matches(db):
    pl = playlist.Playlist(slug='playlist-one', session=db)
    assert pl.add('UNKLE',) == 0


def test_delete(db):
    pl = playlist.Playlist(slug='playlist-one', session=db)
    expected = pl.record.id
    assert pl.delete() == expected
    assert not pl.exists
    assert pl.deleted


def test_delete_playlist_not_exist(db):
    pl = playlist.Playlist(slug='playlist-doesnt-exist', session=db, create_ok=False)
    assert not pl.delete()
    assert not pl.exists
    assert not pl.deleted


def test_cannot_create_after_delete(db):
    pl = playlist.Playlist(slug='playlist-one', session=db)
    pl.delete()
    with pytest.raises(RuntimeError):
        assert pl.record
    assert not pl.exists


def test_entries(db):
    pl = playlist.Playlist(slug='playlist-one', session=db)
    # assert twice for branch coverage of cached values
    assert pl.entries
    assert pl.entries


def test_playlist_not_exist_formatted(db):
    pl = playlist.Playlist(slug='fnord', session=db, create_ok=False)
    assert not repr(pl)
    assert not pl.as_dict


def test_playlist_formatted(db):
    pl = playlist.Playlist(slug='playlist-one', session=db)
    assert repr(pl)
    assert pl.as_string
    assert pl.as_dict


