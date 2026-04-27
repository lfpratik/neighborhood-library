Create SQLAlchemy async model for "$ARGUMENTS" entity.

1. Read the "$ARGUMENTS" table definition in CLAUDE.md under "Data Model — Entity Definitions" for exact columns, types, and constraints.
2. Read app/domain/$ARGUMENTS.py for status enums and transitions.
3. Follow SQLAlchemy conventions in CLAUDE.md (mapped_column, Mapped types, Base class).
4. Place in app/database/models/$ARGUMENTS.py.
5. Import and register in app/database/models/__init__.py.
6. Add SQLAlchemy relationships (e.g., Book.borrows, Member.borrows, Borrow.book, Borrow.member).
