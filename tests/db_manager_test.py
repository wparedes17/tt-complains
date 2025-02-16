import pytest
from sqlalchemy.orm import Session
from db.db_manager import MySQLManager
from models.db_models import Base, Node, TrailerDriver


@pytest.fixture
def db_manager():
    """Create a test database manager using SQLite for testing"""
    manager = MySQLManager("sqlite:///:memory:")
    manager.init_db(Base)
    return manager


@pytest.fixture
def sample_data(db_manager):
    """Create sample data for testing"""
    with db_manager.session_scope() as session:
        node = Node(node_id=1, name="Test Node")
        session.add(node)

        driver = TrailerDriver(
            driver_id=1,
            age=30,
            sex='M',
            location_id=1,
            status='active',
            salary=50000.0,
            experience=5
        )
        session.add(driver)
    return db_manager


def test_db_initialization(db_manager):
    """Test database initialization"""
    assert db_manager.get_engine() is not None


def test_session_scope(db_manager):
    """Test session creation and management"""
    with db_manager.session_scope() as session:
        assert isinstance(session, Session)


def test_session_rollback(db_manager):
    """Test session rollback on error"""
    try:
        with db_manager.session_scope() as session:
            node = Node(node_id=1, name="Test Node")
            session.add(node)
            raise Exception("Test rollback")
    finally:
        with db_manager.session_scope() as session:
            assert session.query(Node).count() == 0