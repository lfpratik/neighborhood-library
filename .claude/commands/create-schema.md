Create Pydantic v2 schemas for "$ARGUMENTS" entity.

1. Read CLAUDE.md "Data Model — Entity Definitions" for the "$ARGUMENTS" table fields.
2. Read app/domain/$ARGUMENTS.py for status enums.
3. Follow Pydantic conventions in CLAUDE.md (ConfigDict, from_attributes).
4. Create: {Entity}Create (input), {Entity}Update (partial), {Entity}Response (output), {Entity}StatusUpdate (status change).
5. Place in app/api/schemas/$ARGUMENTS.py.
6. If another schema file exists already, follow that exact pattern.
