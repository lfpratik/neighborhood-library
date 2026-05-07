from collections.abc import Generator

from fastapi import Depends

from app.database.unit_of_work import UnitOfWork
from app.services.book_service import BookService
from app.services.borrow_service import BorrowService
from app.services.member_service import MemberService


def get_uow() -> Generator[UnitOfWork, None, None]:
    with UnitOfWork() as uow:
        yield uow


def get_book_service(uow: UnitOfWork = Depends(get_uow)) -> BookService:
    return BookService(uow)


def get_member_service(uow: UnitOfWork = Depends(get_uow)) -> MemberService:
    return MemberService(uow)


def get_borrow_service(uow: UnitOfWork = Depends(get_uow)) -> BorrowService:
    return BorrowService(uow)
