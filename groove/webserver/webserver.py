import logging
import json
import os

import bottle
from bottle import HTTPResponse, template, static_file
from bottle.ext import sqlalchemy

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


@server.route('/build')
@bottle.auth_basic(is_authenticated)
def build():
    return "Authenticated. Groovy."


@server.route('/static/<filepath:path>')
def server_static(filepath):
    theme = themes.load_theme()
    asset = theme.path / groove.path.theme_static(filepath)
    if asset.exists():
        root = asset.parent
    else:
        root = groove.path.static_root()
        asset = groove.path.static(filepath)
    if asset.is_dir():
        logging.warning("Asset {asset} is a directory; returning 404.")
        return HTTPResponse(status=404, body="Not found.")
    logging.debug(f"Serving asset {asset.name} from {root}")
    return static_file(asset.name, root=root)


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

    path = groove.path.media(track['relpath'])
    if path.exists:
        return static_file(path.name, root=path.parent)
    else:
        return HTTPResponse(status=404, body="Not found")


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
