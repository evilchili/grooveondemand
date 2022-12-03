import logging
import os
import typer

from pathlib import Path
from typing import Optional, List
from dotenv import load_dotenv
from slugify import slugify
from rich import print
import rich.table

from groove.shell import interactive_shell
from groove.playlist import Playlist
from groove import db
from groove.db.manager import database_manager
from groove.db.scanner import media_scanner
from groove.webserver import webserver

playlist_app = typer.Typer()
app = typer.Typer()
app.add_typer(playlist_app, name='playlist', help='Manage playlists.')


def initialize():
    load_dotenv()
    debug = os.getenv('DEBUG', None)
    logging.basicConfig(format='%(asctime)s - %(message)s',
                        level=logging.DEBUG if debug else logging.INFO)


@playlist_app.command()
def list():
    """
    List all Playlists
    """
    initialize()
    with database_manager() as manager:
        query = manager.session.query(db.playlist)
        table = rich.table.Table(
            *[rich.table.Column(k.name.title()) for k in db.playlist.columns]
        )
        for row in db.windowed_query(query, db.playlist.c.id, 1000):
            columns = tuple(Playlist.from_row(row, manager.session).record)[0:-1]
            table.add_row(*[str(col) for col in columns])
        print()
        print(table)
        print()


@playlist_app.command()
def delete(
    name: str = typer.Argument(
        ...,
        help="The name of the playlist to create."
    ),
    no_dry_run: bool = typer.Option(
        False,
        help="If True, actually delete the playlist, Otherwise, show what would be deleted."
    )
):
    """
    Delete a playlist
    """
    initialize()
    with database_manager() as manager:
        pl = Playlist(slug=slugify(name), session=manager.session, create_if_not_exists=False)
        if not pl.exists:
            logging.info(f"No playlist named '{name}' could be found.")
            return

        if no_dry_run is False:
            entry_count = 0 if not pl.entries else len([e for e in pl.entries])
            print(f"Would delete playlist {pl.record.id}, which contains {entry_count} tracks.")
            return
        deleted_playlist = pl.delete()
        print(f"Playlist {deleted_playlist} deleted.")


@playlist_app.command()
def get(
    slug: str = typer.Argument(
        ...,
        help="The slug of the playlist to retrieve."
    ),
):
    initialize()
    with database_manager() as manager:
        pl = Playlist(slug=slug, session=manager.session)
        print(pl.as_dict)


@playlist_app.command()
def add(
    name: str = typer.Argument(
        ...,
        help="The name of the playlist to create."
    ),
    description: str = typer.Option(
        None,
        help="The description of the playlist."
    ),
    tracks: List[str] = typer.Option(
        None,
        help="A list of tracks to add to the playlist."
    ),
    exists_ok: bool = typer.Option(
        True,
        help="If True, it is okay if the playlist already exists."
    ),
    multiples_ok: bool = typer.Option(
        False,
        help="If True, the same track can be added to the playlist multiple times."
    )
):
    """
    Create a new playlist with the specified name, unless it already exists.
    """
    initialize()
    with database_manager() as manager:
        pl = Playlist(
            slug=slugify(name),
            session=manager.session,
            name=name,
            description=description,
            create_if_not_exists=True)
        if pl.exists:
            if not exists_ok:
                raise RuntimeError(f"Playlist with slug {pl.slug} already exists!")
        logging.debug(pl.as_dict)
        if tracks:
            pl.add(tracks)
    print(pl.as_dict)


@app.command()
def scan(
    root: Optional[Path] = typer.Option(
        None,
        help="The path to the root of your media."
    ),
    debug: bool = typer.Option(
        False,
        help='Enable debugging output'
    ),
):
    """
    Scan the filesystem and create track entries in the database.
    """
    initialize()
    with database_manager() as manager:
        scanner = media_scanner(root=root, db=manager.session)
        count = scanner.scan()
        logging.info(f"Imported {count} new tracks.")


@app.command()
def shell():
    initialize()
    interactive_shell.start()


@app.command()
def server(
    host: str = typer.Argument(
        '0.0.0.0',
        help="bind address",
    ),
    port: int = typer.Argument(
        2323,
        help="bind port",
    ),
    debug: bool = typer.Option(
        False,
        help='Enable debugging output'
    ),
):
    """
    Start the Groove on Demand playlsit server.
    """
    initialize()
    print("Starting Groove On Demand...")
    with database_manager() as manager:
        manager.import_from_filesystem()
    webserver.start(host=host, port=port, debug=debug)


if __name__ == '__main__':
    app()
