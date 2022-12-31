import io
import logging
import os
import sys
import typer

from pathlib import Path
from typing import Optional
from textwrap import dedent

from dotenv import load_dotenv
from rich import print
from rich.logging import RichHandler

import groove.path

from groove.shell import interactive_shell
from groove.db.manager import database_manager
from groove.webserver import webserver
from groove.exceptions import ConfigurationError
from groove.console import Console

SETUP_HELP = """
# Please make sure you set MEDIA_ROOT and SECRET_KEY in your environment.
# By default, Groove on Demand will attempt to load these variables from
# ~/.groove/defaults, which may contain the following variables as well. See
# also the --root paramter.

# Set this one. The path containing your media files
MEDIA_ROOT=

# the kinds of files to import
MEDIA_GLOB=*.mp3,*.flac,*.m4a

# If defined, transcode media before streaming it, and cache it to disk. The
# strings INFILE and OUTFILE will be replaced with the media source file and
# the cached output location, respectively. The default below uses ffmpeg to
# transcode to webm with a reasonable trade-off between file size and quality.
TRANSCODER=/usr/bin/ffmpeg -i INFILE -c:v libvpx-vp9 -crf 30 -b:v 0 -b:a 256k -c:a libopus OUTFILE

# where to cache transcoded media files
CACHE_ROOT=~/.groove/cache

# where to store the groove_on_demand.db sqlite database.
DATABASE_PATH=~

# Try 'groove themes' to see a list of available themes.
DEFAULT_THEME=blue_train

# Web interface configuration
HOST=127.0.0.1
PORT=2323

# Set this to a suitably random string.
SECRET_KEY=

# Console configuration
EDITOR=vim
CONSOLE_WIDTH=auto
"""

app = typer.Typer()


@app.callback()
def main(
    context: typer.Context,
    root: Optional[Path] = typer.Option(
        Path('~/.groove'),
        help="Path to the Groove on Demand environment",
    )
):
    load_dotenv(root.expanduser() / Path('defaults'))
    load_dotenv(stream=io.StringIO(SETUP_HELP))
    debug = os.getenv('DEBUG', None)
    logging.basicConfig(
        format='%(message)s',
        level=logging.DEBUG if debug else logging.INFO,
        handlers=[
            RichHandler(rich_tracebacks=True, tracebacks_suppress=[typer])
        ]
    )
    logging.getLogger('asyncio').setLevel(logging.ERROR)

    try:
        groove.path.media_root()
        groove.path.static_root()
        groove.path.themes_root()
        groove.path.database()
    except ConfigurationError as e:
        sys.stderr.write(f'{e}\n\n{SETUP_HELP}')
        sys.exit(1)


@app.command()
def setup(context: typer.Context):
    """
    (Re)Initialize Groove on Demand.
    """
    sys.stderr.write("Interactive setup is not yet available. Sorry!\n")
    print(dedent(SETUP_HELP))


@app.command()
def themes(context: typer.Context):
    """
    List the available themes.
    """
    print("Available themes:")
    themes = [theme for theme in groove.path.themes_root().iterdir()]
    tags = ('artist', 'title', 'bold', 'dim', 'link', 'prompt', 'bright', 'text', 'help')
    for theme in themes:
        text = ''
        for tag in tags:
            text += f'[{tag}]◼◼◼◼◼◼'
        Console(theme=theme.name).print(f' ▪ [title]{theme.name}[/title] {text}')


@app.command()
def playlists(context: typer.Context):
    """
    List all playlists
    """
    with database_manager() as manager:
        shell = interactive_shell.InteractiveShell(manager)
        shell.list(None)


@app.command()
def scan(
    context: typer.Context,
    path: Optional[Path] = typer.Option(
        '',
        help="A path to scan, relative to your MEDIA_ROOT. "
             "If not specified, the entire MEDIA_ROOT will be scanned."
    ),
):
    """
    Scan the filesystem and create track entries in the database.
    """
    with database_manager() as manager:
        shell = interactive_shell.InteractiveShell(manager)
        shell.console.print("Starting the Groove on Demand scanner...")
        shell.scan([str(path)])


@app.command()
def shell(context: typer.Context):
    """
    Start the Groove on Demand interactive shell.
    """
    with database_manager() as manager:
        interactive_shell.InteractiveShell(manager).start()


@app.command()
def server(
    context: typer.Context,
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
    with database_manager() as manager:
        manager.import_from_filesystem()
    webserver.start(host=host, port=port, debug=debug)


if __name__ == '__main__':
    app()
