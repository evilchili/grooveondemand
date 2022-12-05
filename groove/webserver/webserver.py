import logging
import json
import os

import bottle
from bottle import HTTPResponse, template, static_file
from bottle.ext import sqlalchemy
from sqlalchemy.exc import NoResultFound, MultipleResultsFound

import groove.db
from groove.auth import is_authenticated
from groove.db.manager import database_manager
from groove.playlist import Playlist
from groove.webserver import requests, themes

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


def serve(template_name, theme=None, **template_args):
    theme = themes.load_theme(theme)
    return HTTPResponse(status=200, body=template(
        str(theme.path / groove.path.theme_template(template_name)),
        url=requests.url(),
        theme=theme,
        **template_args
    ))


@server.route('/')
def index():
    return "Groovy."


@server.route('/static/<filepath:path>')
def serve_static(filepath):
    theme = themes.load_theme()
    path = groove.path.static(filepath, theme=theme)
    logging.debug(f"Serving asset {path.name} from {path.parent}")
    return static_file(path.name, root=path.parent)


@server.route('/track/<request>/<track_id>')
def serve_track(request, track_id, db):

    expected = requests.encode([track_id], '/track')
    if not requests.verify(request, expected):  # pragma: no cover
        return HTTPResponse(status=404, body="Not found")

    try:
        track_id = int(track_id)
        track = db.query(groove.db.track).filter(
            groove.db.track.c.id == track_id
        ).one()
    except (NoResultFound, MultipleResultsFound):
        return HTTPResponse(status=404, body="Not found")

    path = groove.path.media(track['relpath'])
    logging.debug(f"Service track {path.name} from {path.parent}")
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

    return serve('playlist', playlist=pl)


@server.route('/build')
@bottle.auth_basic(is_authenticated)
def build():
    return "Authenticated. Groovy."


@bottle.auth_basic(is_authenticated)
@server.route('/build/search/playlist/<slug>')
def search_playlist(slug, db):
    playlist = Playlist(slug=slug, session=db, create_ok=False).load()
    if not playlist.record:
        logging.debug(f"Playist {slug} doesn't exist.")
        body = {}
    else:
        body = json.dumps(playlist.as_dict)
    return HTTPResponse(status=200, content_type='application/json', body=body)
