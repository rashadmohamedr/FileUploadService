"""
Test configuration and fixtures for pytest.
This file contains shared fixtures used across all tests.
"""
import os
import sys
import tempfile
import shutil
import uuid
from typing import Generator
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session
from faker import Faker

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.main import app
from app.db.database import Base 
from app.dependencies import get_db
from app.models.user import User
from app.models.file import File
from app.core.security import hash_password
from app.core.config import settings

# Initialize Faker for generating test data
fake = Faker()

# Test database URL (use in-memory SQLite for tests)
TEST_DATABASE_URL = "sqlite:///./test.db"

@pytest.fixture(scope="session")
def test_engine():
    """Create a test database engine."""
    # Ensure a clean slate by removing existing test database
    if os.path.exists("test.db"):
        try:
            os.remove("test.db")
        except PermissionError:
            print("Warning: Could not remove existing test.db at start of session")
            
    engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)
    # Dispose the engine to release the file lock (crucial on Windows)
    engine.dispose()
    
    # Clean up test database file
    if os.path.exists("test.db"):
        try:
            os.remove("test.db")
        except PermissionError:
            pass  # If still locked, we can't delete it

            

@pytest.fixture(scope="function")
def db_session(test_engine) -> Generator[Session, None, None]:
    """Create a new database session for each test with rollback."""
    connection = test_engine.connect()
    transaction = connection.begin()
    
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=connection)
    session = SessionLocal()
    
    # Begin a nested transaction (SAVEPOINT).
    # This ensures that session.commit() in the code only commits to this savepoint,
    # which is rolled back at the end of the test.
    session.begin_nested()

    # If the application code calls session.commit, it will end the nested transaction.
    # We need to start a new one immediately to keep the test isolated.
    @event.listens_for(session, "after_transaction_end")
    def restart_savepoint(session, transaction):
        if transaction.nested and not transaction._parent.nested:
            session.expire_all()
            session.begin_nested()
            
    try:
        yield session
    finally:
        session.close()
        transaction.rollback()
        connection.close()

        # Explicitly clean tables to ensure isolation even if rollback failed
        # This is a safety net for SQLite file persistence issues
        with test_engine.connect() as conn:
            for table in reversed(Base.metadata.sorted_tables):
                conn.execute(table.delete())
            conn.commit()

@pytest.fixture(scope="function")
def client(db_session: Session) -> Generator[TestClient, None, None]:
    """Create a test client with overridden database dependency."""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()

@pytest.fixture(scope="function")
def test_user(db_session: Session) -> User:
    """Create a test user in the database."""
    user = User(
        username=fake.user_name(),
        email=fake.email(),
        password=hash_password("TestPassword123!"),
        is_admin=False,
        total_storage_used=0.0
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user

@pytest.fixture(scope="function")
def test_admin(db_session: Session) -> User:
    """Create a test admin user in the database."""
    admin = User(
        username="admin_" + fake.user_name(),
        email="admin_" + fake.email(),
        password=hash_password("AdminPassword123!"),
        is_admin=True,
        total_storage_used=0.0
    )
    db_session.add(admin)
    db_session.commit()
    db_session.refresh(admin)
    return admin

@pytest.fixture(scope="function")
def test_upload_dir() -> Generator[str, None, None]:
    """Create a temporary upload directory for tests."""
    temp_dir = tempfile.mkdtemp()
    original_upload_dir = settings.UPLOAD_DIR
    settings.UPLOAD_DIR = temp_dir
    yield temp_dir
    # Clean up
    settings.UPLOAD_DIR = original_upload_dir
    if os.path.exists(temp_dir):
        shutil.rmtree(temp_dir)

@pytest.fixture
def sample_file_content() -> bytes:
    """Generate sample file content for testing."""
    return b"This is a test file content for upload testing."

@pytest.fixture
def sample_image_content() -> bytes:
    """Generate a simple PNG image content for testing."""
    # This is a minimal valid PNG file (1x1 transparent pixel)
    return (
        b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01'
        b'\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\nIDATx\x9cc\x00\x01'
        b'\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82'
    )

@pytest.fixture
def test_file(db_session: Session, test_user: User, test_upload_dir: str) -> File:
    """Create a test file in the database and on disk."""
    unique_name = f"{uuid.uuid4()}.txt"
    file_content = b"Test file content"
    file_path = os.path.join(test_upload_dir, unique_name)
    
    with open(file_path, "wb") as f:
        f.write(file_content)
    
    db_file = File(
        saved_name=unique_name,
        uploaded_name="original_test.txt",
        owner_id=test_user.id,
        content_type="text/plain",
        path=file_path,
        size=len(file_content) / (1024 * 1024)
    )
    db_session.add(db_file)
    db_session.commit()
    db_session.refresh(db_file)
    return db_file

@pytest.fixture
def auth_headers(test_user: User) -> dict:
    """Generate authentication headers for API requests."""
    # TODO: Replace with actual JWT token generation once implemented
    return {"Authorization": f"Bearer fake_token_for_{test_user.id}"}

@pytest.fixture
def multiple_test_users(db_session: Session) -> list[User]:
    """Create multiple test users for testing admin features."""
    users = []
    for _ in range(5):
        user = User(
            username=fake.user_name(),
            email=fake.email(),
            password=hash_password("TestPassword123!"),
            is_admin=False,
            total_storage_used=fake.random_int(min=0, max=1000000)
        )
        db_session.add(user)
        users.append(user)
    db_session.commit()
    return users
