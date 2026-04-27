from collections.abc import Generator

from fastapi import Depends
from sqlalchemy.orm import Session

from app.database.repositories.book_repository import BookRepository
from app.database.repositories.borrow_repository import BorrowRepository
from app.database.repositories.member_repository import MemberRepository
from app.database.session import SessionLocal
from app.services.book_service import BookService
from app.services.borrow_service import BorrowService
from app.services.member_service import MemberService


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_book_repository(db: Session = Depends(get_db)) -> BookRepository:
    return BookRepository(db)


def get_book_service(
    repo: BookRepository = Depends(get_book_repository),
) -> BookService:
    return BookService(repo)


def get_member_repository(db: Session = Depends(get_db)) -> MemberRepository:
    return MemberRepository(db)


def get_member_service(
    repo: MemberRepository = Depends(get_member_repository),
) -> MemberService:
    return MemberService(repo)


def get_borrow_repository(db: Session = Depends(get_db)) -> BorrowRepository:
    return BorrowRepository(db)


def get_borrow_service(
    borrow_repo: BorrowRepository = Depends(get_borrow_repository),
    book_repo: BookRepository = Depends(get_book_repository),
    member_repo: MemberRepository = Depends(get_member_repository),
) -> BorrowService:
    return BorrowService(borrow_repo, book_repo, member_repo)
