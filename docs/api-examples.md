# API Examples

All examples assume the server is running at `http://localhost:8000`.

---

## Books

### Add a book

```bash
curl -s -X POST http://localhost:8000/api/v1/books \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Clean Code",
    "author": "Robert C. Martin",
    "isbn": "9780132350884",
    "genre": "Software Engineering",
    "publication_year": 2008
  }' | jq .
```

### List all available books

```bash
curl -s "http://localhost:8000/api/v1/books?status=available&page=1&size=20" | jq .
```

### Search books by title/author

```bash
curl -s "http://localhost:8000/api/v1/books?search=fowler" | jq .
```

### Get a specific book

```bash
curl -s "http://localhost:8000/api/v1/books/<book_id>" | jq .
```

### Update book info

```bash
curl -s -X PUT http://localhost:8000/api/v1/books/<book_id> \
  -H "Content-Type: application/json" \
  -d '{"publisher": "Prentice Hall", "publication_year": 2008}' | jq .
```

### Retire a book

```bash
curl -s -X PATCH http://localhost:8000/api/v1/books/<book_id>/status \
  -H "Content-Type: application/json" \
  -d '{"status": "retired"}' | jq .
```

---

## Members

### Register a member

```bash
curl -s -X POST http://localhost:8000/api/v1/members \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Alice Johnson",
    "email": "alice@example.com",
    "phone": "555-1234"
  }' | jq .
```

### List active members

```bash
curl -s "http://localhost:8000/api/v1/members?status=active" | jq .
```

### Search members by name or email

```bash
curl -s "http://localhost:8000/api/v1/members?search=alice" | jq .
```

### Get a specific member

```bash
curl -s "http://localhost:8000/api/v1/members/<member_id>" | jq .
```

### Suspend a member

```bash
curl -s -X PATCH http://localhost:8000/api/v1/members/<member_id>/status \
  -H "Content-Type: application/json" \
  -d '{"status": "suspended"}' | jq .
```

### Reactivate a member

```bash
curl -s -X PATCH http://localhost:8000/api/v1/members/<member_id>/status \
  -H "Content-Type: application/json" \
  -d '{"status": "active"}' | jq .
```

---

## Borrows

### Borrow a book

```bash
curl -s -X POST http://localhost:8000/api/v1/borrows \
  -H "Content-Type: application/json" \
  -d '{
    "book_id": "<book_id>",
    "member_id": "<member_id>",
    "notes": "Picked up at front desk"
  }' | jq .
```

### Return a book

```bash
curl -s -X PATCH http://localhost:8000/api/v1/borrows/<borrow_id>/return | jq .
```

### List all active borrows

```bash
curl -s "http://localhost:8000/api/v1/borrows?active=true" | jq .
```

### List overdue borrows

```bash
curl -s "http://localhost:8000/api/v1/borrows?overdue=true" | jq .
```

### List borrows for a specific member

```bash
curl -s "http://localhost:8000/api/v1/borrows?member_id=<member_id>" | jq .
```

### List borrows for a specific book

```bash
curl -s "http://localhost:8000/api/v1/borrows?book_id=<book_id>" | jq .
```

### Get a specific borrow

```bash
curl -s "http://localhost:8000/api/v1/borrows/<borrow_id>" | jq .
```

---

## System

### Health check

```bash
curl -s http://localhost:8000/api/v1/health | jq .
# {"status": "ok", "database": "ok"}
```

---

## End-to-End Flow

This sequence demonstrates a full borrow-and-return cycle:

```bash
BASE="http://localhost:8000/api/v1"

# 1. Create a book
BOOK=$(curl -s -X POST "$BASE/books" \
  -H "Content-Type: application/json" \
  -d '{"title": "Refactoring", "author": "Martin Fowler", "isbn": "9780134757599"}')
BOOK_ID=$(echo $BOOK | jq -r .id)
echo "Book: $BOOK_ID"

# 2. Create a member
MEMBER=$(curl -s -X POST "$BASE/members" \
  -H "Content-Type: application/json" \
  -d '{"name": "Alice Johnson", "email": "alice2@example.com"}')
MEMBER_ID=$(echo $MEMBER | jq -r .id)
echo "Member: $MEMBER_ID"

# 3. Borrow the book
BORROW=$(curl -s -X POST "$BASE/borrows" \
  -H "Content-Type: application/json" \
  -d "{\"book_id\": \"$BOOK_ID\", \"member_id\": \"$MEMBER_ID\"}")
BORROW_ID=$(echo $BORROW | jq -r .id)
echo "Borrow: $BORROW_ID  Due: $(echo $BORROW | jq -r .due_date)"

# 4. Confirm book is now "borrowed"
curl -s "$BASE/books/$BOOK_ID" | jq .status

# 5. Return the book
curl -s -X PATCH "$BASE/borrows/$BORROW_ID/return" | jq .returned_at

# 6. Confirm book is "available" again
curl -s "$BASE/books/$BOOK_ID" | jq .status
```

---

## Error Responses

All errors follow this format:

```json
{
  "detail": {
    "code": "BookNotAvailableError",
    "message": "Book is currently borrowed"
  }
}
```

### Common error codes

| HTTP | Code | Trigger |
|------|------|---------|
| 404  | `BookNotFoundError` | Book ID does not exist |
| 404  | `MemberNotFoundError` | Member ID does not exist |
| 404  | `BorrowNotFoundError` | Borrow ID does not exist |
| 409  | `BookNotAvailableError` | Borrowing a retired or already-borrowed book |
| 409  | `BookRetirementError` | Retiring a currently-borrowed book |
| 409  | `BookAlreadyBorrowedError` | Book already has an active borrow record |
| 409  | `BookAlreadyReturnedError` | Returning a borrow that is already closed |
| 409  | `MemberNotActiveError` | Inactive or suspended member trying to borrow |
| 422  | _(Pydantic)_ | Request body fails schema validation |

---

## Postman & Insomnia

FastAPI automatically generates an OpenAPI spec — both tools can import it directly, saving you from writing collections by hand.

### Import via OpenAPI URL (recommended)

Start the server first (`make demo` or `make dev`), then:

**Postman**
1. Open Postman → **Import** (top-left)
2. Select **Link** tab
3. Paste: `http://localhost:8000/openapi.json`
4. Click **Continue** → **Import**
5. A collection named *Neighborhood Library API* appears with all endpoints pre-configured

**Insomnia**
1. Open Insomnia → **Create** → **Import**
2. Select **From URL**
3. Paste: `http://localhost:8000/openapi.json`
4. Click **Fetch and Import**
5. All endpoints are imported under a new collection

### Set a base URL variable

After importing, set a variable so you don't hardcode the host in every request:

**Postman** — go to the collection → **Variables** tab → add:
| Variable | Initial value | Current value |
|----------|---------------|---------------|
| `base_url` | `http://localhost:8000/api/v1` | `http://localhost:8000/api/v1` |

**Insomnia** — go to **Manage Environments** → add:
```json
{
  "base_url": "http://localhost:8000/api/v1"
}
```

### Download the spec as a file

If you prefer a local file instead of a URL:

```bash
curl -s http://localhost:8000/openapi.json -o openapi.json
```

Then import the saved `openapi.json` file using **Import → File** in either tool.
