Create FastAPI route file for "$ARGUMENTS" resource.

1. Read CLAUDE.md "Endpoints" table for the exact "$ARGUMENTS" endpoints, methods, and status codes.
2. Read CLAUDE.md "Query Parameters" for filter/pagination params.
3. Follow FastAPI conventions in CLAUDE.md (Depends, status codes, Location header on POST).
4. Follow the "Route Pattern" example in CLAUDE.md.
5. Place in app/api/routes/$ARGUMENTS.py.
6. Register router in app/main.py with prefix /api/v1.
7. If another route file exists already, follow that exact pattern.
