import logging
import json
import os
from pathlib import Path

import bottle
from bottle import HTTPResponse, template, static_file
from bottle.ext import sqlalchemy

import groove.db
from groove.auth import is_authenticated
from groove.db.manager import database_manager
from groove.playlist import Playlist
from groove.webserver import requests

#  from groove.exceptions import APIHandlingException

server = bottle.Bottle()


def start(host: str, port: int, debug: bool) -> None:  # pragma: no cover
    """
    Start the Bottle app.
    """
    logging.debug(f"Configuring sqllite using {os.environ.get('DATABASE_PATH')}")

    with database_manager() as manager:
        server.install(sqlalchemy.Plugin(
            manager.engine,
            groove.db.metadata,
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


@server.route('/static/<filepath:path>')
def server_static(filepath):
    return static_file(filepath, root='static')


@bottle.auth_basic(is_authenticated)
@server.route('/build/search/playlist')
def search_playlist(slug, db):
    playlist = Playlist(slug=slug, session=db, create_ok=False)
    response = json.dumps(playlist.as_dict)
    logging.debug(response)
    return HTTPResponse(status=200, content_type='application/json', body=response)


@server.route('/track/<request>/<track_id>')
def serve_track(request, track_id, db):

    expected = requests.encode([track_id], '/track')
    if not requests.verify(request, expected):
        return HTTPResponse(status=404, body="Not found")

    track_id = int(track_id)
    track = db.query(groove.db.track).filter(
        groove.db.track.c.id == track_id
    ).one()

    path = Path(os.environ['MEDIA_ROOT']) / Path(track['relpath'])
    return static_file(path.name, root=path.parent)


@server.route('/playlist/<slug>')
def serve_playlist(slug, db):
    """
    Retrieve a playlist and its entries by a slug.
    """
    logging.debug(f"Looking up playlist: {slug}...")
    playlist = Playlist(slug=slug, session=db, create_ok=False).load()
    if not playlist.record:
        logging.debug(f"Playist {slug} doesn't exist.")
        return HTTPResponse(status=404, body="Not found")
    logging.debug(f"Loaded {playlist.record}")
    logging.debug(playlist.as_dict['entries'])

    pl = playlist.as_dict

    for entry in pl['entries']:
        sig = requests.encode([str(entry['track_id'])], uri='/track')
        entry['url'] = f"/track/{sig}/{entry['track_id']}"

    template_path = Path(os.environ['TEMPLATE_PATH']) / Path('playlist.tpl')
    body = template(
        str(template_path),
        url=requests.url(),
        playlist=pl
    )
    return HTTPResponse(status=200, body=body)
