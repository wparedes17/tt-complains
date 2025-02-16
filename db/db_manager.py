# db/db_manager.py
from typing import Generator
from logger.logger import logger
from contextlib import contextmanager
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import SQLAlchemyError

class MySQLManager:
    def __init__(self, db_string_credentials: str):
        """
        Initialize MySQL Manager

        Args:
            db_string_credentials (str): Database connection string

        Example:
            db_string = "mysql+pymysql://user:password@localhost/db_name"
        """
        self._string_connection = db_string_credentials
        self._engine = None
        self._session_maker = None

    def _connection(self):
        try:
            self._engine = create_engine(
                self._string_connection,
                pool_size=5,
                max_overflow=10,
                pool_timeout=30,
                pool_recycle=3600
            )
            self._session_maker = sessionmaker(bind=self._engine)
            return True
        except SQLAlchemyError as e:
            logger.error(f"Failed to create connection database: {str(e)}")
            return False

    def init_db(self, base_engine) -> bool:
        """
        Initialize the database with all tables

        Args:
            base_engine: SQLAlchemy declarative base instance

        Returns:
            bool: True if initialization was successful, False otherwise
        """
        try:
            self._connection()
            base_engine.metadata.create_all(self._engine)
            return True
        except SQLAlchemyError as e:
            logger.error(f"Failed to initialize database: {str(e)}")
            return False

    @contextmanager
    def session_scope(self) -> Generator[Session, None, None]:
        """
        Provide a transactional scope around a series of operations.

        Yields:
            Session: SQLAlchemy session

        Example:
            with manager.session_scope() as session:
                session.add(some_object)
        """

        if self._session_maker is None:
            self._connection()

        session = self._session_maker()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Session error: {str(e)}")
            raise
        finally:
            session.close()

    def get_engine(self):
        """Get the SQLAlchemy engine"""
        return self._engine

    def close(self):
        """Close the database connection"""
        if self._engine:
            self._engine.dispose()