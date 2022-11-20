import pytest

import os
import sys

import atheris
import bottle
from boddle import boddle

from groove import ondemand


@pytest.fixture(autouse=True, scope='session')
def init_db():
    ondemand.initialize()


def test_server():
    with boddle():
        ondemand.index()
        assert bottle.response.status_code == 200


def test_auth_with_valid_credentials():
    with boddle(auth=(os.environ.get('USERNAME'), os.environ.get('PASSWORD'))):
        ondemand.build()
        assert bottle.response.status_code == 200


def test_auth_random_input():

    def auth(fuzzed_input):
        with boddle(auth=(fuzzed_input, fuzzed_input)):
            response = ondemand.build()
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
        response = ondemand.get_playlist(slug, db)
        assert response.status_code == expected


def test_playlist_on_empty_db(in_memory_db):
    with boddle():
        response = ondemand.get_playlist('some-slug', in_memory_db)
        assert response.status_code == 404
