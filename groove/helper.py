import json
import logging

from bottle import HTTPResponse

from sqlalchemy import bindparam

from groove import db


class PlaylistDatabaseHelper:
    """
    Convenience class for database interactions.
    """
    def __init__(self, connection):
        self._conn = connection

    @property
    def conn(self):
        return self._conn

    def playlist(self, slug: str) -> dict:
        """
        Retrieve a playlist and its entries by its slug.
        """
        playlist = {}

        query = db.playlist.select(db.playlist.c.slug==bindparam('slug'))
        logging.debug(f"playlist: '{slug}' requested. Query: {query}")
        results = self.conn.execute(str(query), {'slug': slug}).fetchone()
        if not results:
            return playlist

        playlist = results
        query = db.entry.select(db.entry.c.playlist_id == bindparam('playlist_id'))
        logging.debug(f"Retrieving playlist entries. Query: {query}")
        entries = self.conn.execute(str(query), {'playlist_id': playlist['id']}).fetchall()

        playlist = dict(playlist)
        playlist['entries'] = [dict(entry) for entry in entries]
        return playlist

    def json_response(self, playlist: dict, status: int = 200) -> HTTPResponse:
        """
        Create an application/json HTTPResponse object out of a playlist and its entries.
        """
        response = json.dumps(playlist)
        logging.debug(response)
        return HTTPResponse(status=status, content_type='application/json', body=response)
