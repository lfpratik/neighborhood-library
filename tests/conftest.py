from datetime import UTC, datetime, timedelta

import pytest
import uuid_utils
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database.models import Base
from app.database.models.book import Book
from app.database.models.borrow import Borrow
from app.database.models.member import Member
from app.database.unit_of_work import UnitOfWork
from app.dependencies import get_uow
from app.main import app


# ------------------------
# Engine
# ------------------------
@pytest.fixture
def db_engine():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    yield engine
    engine.dispose()


@pytest.fixture
def db_session(db_engine):
    connection = db_engine.connect()
    session_local = sessionmaker(bind=connection, autoflush=True)
    session = session_local()
    try:
        yield session
    finally:
        session.close()
        connection.close()


@pytest.fixture
def client(db_session):
    def override_get_uow():
        # DO NOT wrap with UnitOfWork context manager
        # because FastAPI lifecycle is already handling request boundaries
        yield UnitOfWork.with_session(db_session)

    app.dependency_overrides[get_uow] = override_get_uow
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def sample_book(db_session):
    book = Book(
        id=uuid_utils.uuid7(),
        title="Clean Code",
        author="Robert Martin",
        status="available",
    )
    db_session.add(book)
    db_session.flush()
    return book


@pytest.fixture
def sample_member(db_session):
    member = Member(
        id=uuid_utils.uuid7(),
        name="Alice Smith",
        email="alice@example.com",
        status="active",
    )
    db_session.add(member)
    db_session.flush()
    return member


@pytest.fixture
def sample_borrow(db_session, sample_book, sample_member):
    now = datetime.now(UTC)
    borrow = Borrow(
        id=uuid_utils.uuid7(),
        book_id=sample_book.id,
        member_id=sample_member.id,
        borrowed_at=now,
        due_date=now + timedelta(days=14),
    )
    sample_book.status = "borrowed"
    db_session.add(borrow)
    db_session.flush()
    return borrow
