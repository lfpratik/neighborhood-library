from sqlalchemy import text
from sqlalchemy.orm import Session

from app.database.repositories.book_repository import BookRepository
from app.database.repositories.borrow_repository import BorrowRepository
from app.database.repositories.member_repository import MemberRepository
from app.database.session import SessionLocal


class UnitOfWork:
    books: BookRepository
    members: MemberRepository
    borrows: BorrowRepository

    def __init__(self) -> None:
        self._session = SessionLocal()
        self._owns_session = True
        self._init_repos()

    def ping(self) -> None:
        """Lightweight DB connectivity check."""
        self._session.execute(text("SELECT 1"))

    @classmethod
    def with_session(cls, session: Session) -> "UnitOfWork":
        uow = cls.__new__(cls)
        uow._session = session
        uow._owns_session = False
        uow._init_repos()
        return uow

    def _init_repos(self) -> None:
        self.books = BookRepository(self._session)
        self.members = MemberRepository(self._session)
        self.borrows = BorrowRepository(self._session)

    def __enter__(self) -> "UnitOfWork":
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        if not self._owns_session:
            return
        try:
            if exc_type:
                self._session.rollback()
            else:
                self._session.commit()
        finally:
            self._session.close()
