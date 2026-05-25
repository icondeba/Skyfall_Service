from collections.abc import Generator
from uuid import UUID
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

import app.models  # noqa: F401 - register SQLAlchemy models
from app.api.dependencies import get_db
from app.main import app
from app.models.base import Base
from app.repositories.order_repository import OrderRepository


@pytest.fixture
def test_tenant_id() -> UUID:
    return UUID("00000000-0000-0000-0000-000000000001")


@pytest.fixture
def test_db() -> Generator[Session, None, None]:
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
    db = TestingSessionLocal()
    transaction = db.begin()
    try:
        yield db
    finally:
        transaction.rollback()
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture
def mock_order_repo() -> MagicMock:
    return MagicMock(spec=OrderRepository)


@pytest.fixture
def test_client(test_db: Session) -> Generator[TestClient, None, None]:
    def override_get_db() -> Generator[Session, None, None]:
        yield test_db

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as client:
        yield client
    app.dependency_overrides.clear()
