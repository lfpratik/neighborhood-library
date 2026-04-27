Create tests for "$ARGUMENTS".

1. Read CLAUDE.md "Status Lifecycles" and "Borrow Rules" for edge cases to test.
2. Follow testing conventions in CLAUDE.md (pytest-asyncio, httpx.AsyncClient).
3. Test: happy path CRUD, invalid status transitions, conflict scenarios, not-found errors.
4. Use conftest.py fixtures for db session and test client.
5. Add to tests/test_$ARGUMENTS.py.
6. If another test file exists already, follow that exact pattern.
