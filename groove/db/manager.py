import os

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from . import metadata


class DatabaseManager:
    """
    A context manager for working with sqllite database.
    """

    def __init__(self):
        self._engine = None
        self._session = None

    @property
    def engine(self):
        if not self._engine:
            self._engine = create_engine(f"sqlite:///{os.environ.get('DATABASE_PATH')}", future=True)
        return self._engine

    @property
    def session(self):
        if not self._session:
            Session = sessionmaker(bind=self.engine, future=True)
            self._session = Session()
        return self._session

    def import_from_filesystem(self):
        pass

    def __enter__(self):
        metadata.create_all(bind=self.engine)
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        if self.session:
            self.session.close()


database_manager = DatabaseManager()
