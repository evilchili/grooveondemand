import pytest
import sys

import atheris
import bottle
from boddle import boddle
from unittest.mock import MagicMock

from groove.webserver import webserver


def test_server():
    with boddle():
        webserver.index()
        assert bottle.response.status_code == 200


@pytest.mark.parametrize('track_id, expected', [
    ('1', 200),
    ('99', 404)
])
def test_serve_track(monkeypatch, track_id, expected, db):
    monkeypatch.setattr(webserver.requests, 'verify', MagicMock())
    with boddle():
        response = webserver.serve_track('ignored', track_id, db=db)
        assert response.status_code == expected


def test_static_not_from_theme():
    with boddle():
        response = webserver.serve_static('favicon.ico')
        assert response.status_code == 200
        assert response.body.read() == b'favicon.ico\n'


def test_static_from_theme():
    with boddle():
        response = webserver.serve_static('test.css')
        assert response.status_code == 200
        assert response.body.read() == b'/* test.css */\n'


@pytest.mark.parametrize('slug, expected', [
    ('non-existent-slug', False),
    ('playlist-one', True),
])
def test_search_playlist(slug, expected, auth, db):
    with boddle(auth=auth):
        response = webserver.search_playlist(slug, db)
        assert response.status_code == 200

        if expected:
            assert slug in response.body
        else:
            assert response.body == {}


def test_auth_with_valid_credentials(auth):
    with boddle(auth=auth):
        webserver.build()
        assert bottle.response.status_code == 200


@pytest.mark.skip
def test_auth_random_input():
    def auth(fuzzed_input):
        with boddle(auth=(fuzzed_input, fuzzed_input)):
            response = webserver.build()
            assert response.status_code == 401
    atheris.Setup([sys.argv[0], "-atheris_runs=100000"], auth)
    try:
        atheris.Fuzz()
    except SystemExit:
        pass


@pytest.mark.parametrize('slug, expected', [
    ('playlist-one', 200),
    ('playlist-two', 200),
    ('playlist-three', 200),
    ('no such playlist', 404),
])
def test_playlist(db, slug, expected):
    with boddle():
        response = webserver.serve_playlist(slug, db)
        assert response.status_code == expected


def test_playlist_on_empty_db(in_memory_db):
    with boddle():
        response = webserver.serve_playlist('some-slug', in_memory_db)
        assert response.status_code == 404
