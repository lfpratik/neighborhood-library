from app.core.logging import LoggerMixin


class BaseRepository(LoggerMixin):
    """Base class for all repository classes.

    Inheriting from LoggerMixin gives every subclass a self.logger
    bound to the concrete class name. Repository methods use the
    @log_db_call decorator for consistent DB-layer logging — no
    ad-hoc self.logger calls inside repository method bodies.

        class BookRepository(BaseRepository):
            @log_db_call("db_create_book")
            def create(self, data: dict) -> Book:
                ...
    """
