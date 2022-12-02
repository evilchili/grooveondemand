import json
import logging
import os

import bottle
from bottle import HTTPResponse
from bottle.ext import sqlalchemy

from groove.auth import is_authenticated
from groove.db.manager import database_manager
from groove.db import metadata
from groove.playlist import Playlist

server = bottle.Bottle()


def start(host: str, port: int, debug: bool) -> None:  # pragma: no cover
    """
    Start the Bottle app.
    """
    logging.debug(f"Configuring sqllite using {os.environ.get('DATABASE_PATH')}")

    with database_manager() as manager:
        server.install(sqlalchemy.Plugin(
            manager.engine,
            metadata,
            keyword='db',
            create=True,
            commit=True,
        ))
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
    playlist = Playlist(slug=slug, session=db, create_ok=False)
    print(playlist.record)
    if not playlist.exists:
        return HTTPResponse(status=404, body="Not found")
    response = json.dumps(playlist.as_dict)
    logging.debug(response)
    return HTTPResponse(status=200, content_type='application/json', body=response)
