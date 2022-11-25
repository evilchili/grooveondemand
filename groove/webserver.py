import json
import logging
import os

import bottle
from bottle import HTTPResponse
from bottle.ext import sqlite

from groove.auth import is_authenticated
from groove.playlist import Playlist

server = bottle.Bottle()


def start(host: str, port: int, debug: bool) -> None:  # pragma: no cover
    """
    Start the Bottle app.
    """
    logging.debug(f"Configuring sqllite using {os.environ.get('DATABASE_PATH')}")
    server.install(sqlite.Plugin(dbfile=os.environ.get('DATABASE_PATH')))
    logging.debug(f"Configuring webserver with host={host}, port={port}, debug={debug}")
    server.run(
        host=os.getenv('HOST', host),
        port=os.getenv('PORT', port),
        debug=debug,
        server='paste',
        quiet=True
    )


@server.route('/')
def index():
    return "Groovy."


@server.route('/build')
@bottle.auth_basic(is_authenticated)
def build():
    return "Authenticated. Groovy."


@server.route('/playlist/<slug>')
def get_playlist(slug, db):
    """
    Retrieve a playlist and its entries by a slug.
    """
    logging.debug(f"Looking up playlist: {slug}...")
    playlist = Playlist(slug=slug, session=db)
    if not playlist.exists:
        return HTTPResponse(status=404, body="Not found")
    response = json.dumps(playlist.as_dict)
    logging.debug(response)
    return HTTPResponse(status=200, content_type='application/json', body=response)
