from app.core.logging import LoggerMixin


class BaseService(LoggerMixin):
    """Base class for all service classes.

    Inheriting from LoggerMixin gives every subclass a self.logger
    bound to the concrete class name — no __init__ changes required.

        class BookService(BaseService):
            def create_book(self, data: BookCreate) -> Book:
                ...
                self.logger.info("book_created", book_id=str(book.id))
    """
