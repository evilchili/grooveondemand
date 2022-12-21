from prompt_toolkit.completion import Completion, FuzzyCompleter
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import groove.path

from . import metadata


class FuzzyTableCompleter(FuzzyCompleter):

    def __init__(self, table, column, formatter, session):
        self._table = table
        self._column = column
        self._formatter = formatter
        self._session = session

    def get_completions(self, document, complete_event):
        line = document.current_line_before_cursor
        query = self._session.query(self._table).filter(self._column.ilike(f"%{line}%"))
        for row in query.all():
            yield Completion(
                self._formatter(row),
                start_position=-len(line)
            )


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
            path = groove.path.database()
            self._engine = create_engine(f"sqlite:///{path}?check_same_thread=False", future=True)
        return self._engine

    @property
    def session(self):
        if not self._session:
            Session = sessionmaker(bind=self.engine, future=True)
            self._session = Session()
        return self._session

    def import_from_filesystem(self):
        pass

    def fuzzy_table_completer(self, table, column, formatter):
        return FuzzyTableCompleter(table, column, formatter, session=self.session)

    def __enter__(self):
        metadata.create_all(bind=self.engine)
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        if self.session:
            self.session.close()


database_manager = DatabaseManager
