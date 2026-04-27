Create service class for "$ARGUMENTS" entity.

1. Read CLAUDE.md "Status Lifecycles" and "Borrow Rules" for all business logic rules.
2. Read app/domain/$ARGUMENTS.py for entity-specific exceptions and status transitions.
3. Inject repository via constructor. Docstrings on all methods.
4. Validate status transitions using the TRANSITIONS dict from domain/$ARGUMENTS.py.
5. Place in app/services/$ARGUMENTS_service.py.
6. If another service exists already, follow that exact pattern.
