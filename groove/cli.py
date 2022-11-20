import logging
import os
import typer

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from groove import ondemand
from groove.db import metadata


app = typer.Typer()


@app.command()
def initialize():
    load_dotenv()

    # todo: abstract this and replace in_memory_db fixture
    engine = create_engine(f"sqlite:///{os.environ.get('DATABASE_PATH')}", future=True)
    Session = sessionmaker(bind=engine, future=True)
    session = Session()
    metadata.create_all(bind=engine)
    session.close()


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
    load_dotenv()

    ondemand.initialize()

    print("Starting Groove On Demand...")

    debug = os.getenv('DEBUG', None)
    logging.basicConfig(format='%(asctime)s - %(message)s', level=logging.DEBUG if debug else logging.INFO)
    ondemand.server.run(
        host=os.getenv('HOST', host),
        port=os.getenv('PORT', port),
        debug=debug,
        server='paste',
        quiet=True
    )


if __name__ == '__main__':
    app()
