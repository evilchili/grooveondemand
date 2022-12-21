import logging
import os
import typer

from pathlib import Path
from typing import Optional
from dotenv import load_dotenv
from rich.logging import RichHandler

from groove.shell import interactive_shell
from groove.db.manager import database_manager
from groove.webserver import webserver

app = typer.Typer()


def initialize():
    load_dotenv()
    debug = os.getenv('DEBUG', None)
    logging.basicConfig(
        format='%(message)s',
        level=logging.DEBUG if debug else logging.INFO,
        handlers=[
            RichHandler(rich_tracebacks=True, tracebacks_suppress=[typer])
        ]
    )
    logging.getLogger('asyncio').setLevel(logging.ERROR)


@app.command()
def list():
    """
    List all Playlists
    """
    initialize()
    with database_manager() as manager:
        shell = interactive_shell.InteractiveShell(manager)
        shell.list(None)


@app.command()
def scan(
    path: Optional[Path] = typer.Option(
        '',
        help="A path to scan, relative to your MEDIA_ROOT. "
             "If not specified, the entire MEDIA_ROOT will be scanned."
    ),
):
    """
    Scan the filesystem and create track entries in the database.
    """
    initialize()
    with database_manager() as manager:
        shell = interactive_shell.InteractiveShell(manager)
        shell.console.print("Starting the Groove on Demand scanner...")
        shell.scan([str(path)])


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
    with database_manager() as manager:
        manager.import_from_filesystem()
    webserver.start(host=host, port=port, debug=debug)


if __name__ == '__main__':
    app()
