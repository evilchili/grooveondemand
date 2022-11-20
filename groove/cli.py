import logging
import os
import typer

from dotenv import load_dotenv

from groove import webserver
from groove.db.manager import database_manager


app = typer.Typer()


def initialize():
    load_dotenv()
    debug = os.getenv('DEBUG', None)
    logging.basicConfig(format='%(asctime)s - %(message)s',
                        level=logging.DEBUG if debug else logging.INFO)


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
    print("Starting Groove On Demand...")
    initialize()
    with database_manager as manager:
        manager.import_from_filesystem()
    webserver.start(host=host, port=port, debug=debug)


if __name__ == '__main__':
    app()
