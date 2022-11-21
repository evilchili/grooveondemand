import logging
import os
import typer

from pathlib import Path
from typing import Optional
from dotenv import load_dotenv

from groove import webserver
from groove.db.manager import database_manager
from groove.db.scanner import media_scanner


app = typer.Typer()


def initialize():
    load_dotenv()
    debug = os.getenv('DEBUG', None)
    logging.basicConfig(format='%(asctime)s - %(message)s',
                        level=logging.DEBUG if debug else logging.INFO)


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
        logging.info(f"Imported {count} new tracks from {root}.")

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
