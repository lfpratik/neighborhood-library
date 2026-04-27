Create async repository for "$ARGUMENTS" entity.

1. Read CLAUDE.md "Data Model — Entity Definitions" for the "$ARGUMENTS" table fields and indexes.
2. Reference the model in app/database/models/$ARGUMENTS.py.
3. Methods needed: get_by_id, get_all (with pagination, filters from CLAUDE.md "Query Parameters"), create, update.
4. Use AsyncSession, return ORM model instances.
5. Place in app/database/repositories/$ARGUMENTS_repository.py.
6. If another repository exists already, follow that exact pattern.
