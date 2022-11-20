import logging
import os

import bottle
from bottle import HTTPResponse
from bottle.ext import sqlite

from groove.auth import is_authenticated
from groove.helper import PlaylistDatabaseHelper

server = bottle.Bottle()


def initialize():
    """
    Configure the sqlite database.
    """
    server.install(sqlite.Plugin(dbfile=os.environ.get('DATABASE_PATH')))


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
    pldb = PlaylistDatabaseHelper(connection=db)
    playlist = pldb.playlist(slug)
    if not playlist:
        return HTTPResponse(status=404, body="Not found")
    return pldb.json_response(playlist)
