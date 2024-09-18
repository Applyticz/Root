from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import pytest
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)) + '/../')  # Adjust this path if necessary

from app.main import app
from app.db.database import Base, get_db, DATABASE_URL
from app.models.database_models import User, Resume  # Ensure Resume is imported

@pytest.fixture(scope="function")
def overrideDbDepend(dbSession):
    # Override the get_db dependency in FastAPI with the test session
    app.dependency_overrides[get_db] = lambda: dbSession
    yield
    # Remove the override after the test
    app.dependency_overrides.pop(get_db, None)
    
@pytest.fixture(scope="function")
def testClient():
    # Provides a test client for FastAPI
    with TestClient(app) as client:
        yield client
        
@pytest.fixture(scope="function")
def dbSession():
    # Create a new engine connected to the test database
    engine = create_engine(DATABASE_URL.replace('@db', '@localhost'))  # Ensure localhost connection for testing
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    connection = engine.connect()
    transaction = connection.begin()  # Begin a new transaction
    Base.metadata.bind = engine
    
    # Drop all tables and recreate them to ensure a clean state
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    
    db = TestingSessionLocal(bind=connection)
    
    # Optional: Delete all data before starting tests (if tables aren't dropped and recreated)
    db.query(Resume).delete()  # Clean resumes table
    db.query(User).delete()  # Clean users table
    db.commit()

    yield db  # Yield the test database session

    # Rollback the transaction and close the connection after the test
    transaction.rollback()
    connection.close()
