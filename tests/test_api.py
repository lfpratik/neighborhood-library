from datetime import UTC, datetime, timedelta

import uuid_utils

from app.database.models.borrow import Borrow


def test_health_check(client):
    resp = client.get("/api/v1/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


def test_create_book(client):
    resp = client.post("/api/v1/books", json={"title": "Clean Code", "author": "Robert Martin"})
    assert resp.status_code == 201
    data = resp.json()
    assert data["title"] == "Clean Code"
    assert data["status"] == "available"
    assert "Location" in resp.headers


def test_list_books(client):
    client.post("/api/v1/books", json={"title": "Book A", "author": "Author A"})
    client.post("/api/v1/books", json={"title": "Book B", "author": "Author B"})
    resp = client.get("/api/v1/books")
    assert resp.status_code == 200
    data = resp.json()
    assert "items" in data
    assert data["total"] >= 2
    assert data["page"] == 1


def test_get_book_not_found(client):
    fake_id = str(uuid_utils.uuid7())
    resp = client.get(f"/api/v1/books/{fake_id}")
    assert resp.status_code == 404


def test_create_member(client):
    resp = client.post("/api/v1/members", json={"name": "Jane Doe", "email": "jane@example.com"})
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "Jane Doe"
    assert data["status"] == "active"
    assert "Location" in resp.headers


def test_borrow_book(client):
    book = client.post("/api/v1/books", json={"title": "SICP", "author": "Abelson"}).json()
    member = client.post(
        "/api/v1/members", json={"name": "Alice", "email": "alice@example.com"}
    ).json()

    resp = client.post("/api/v1/borrows", json={"book_id": book["id"], "member_id": member["id"]})
    assert resp.status_code == 201
    data = resp.json()
    assert data["book_id"] == book["id"]
    assert data["member_id"] == member["id"]
    assert data["returned_at"] is None


def test_borrow_unavailable(client):
    book = client.post("/api/v1/books", json={"title": "SICP", "author": "Abelson"}).json()
    m1 = client.post("/api/v1/members", json={"name": "Alice", "email": "alice@example.com"}).json()
    m2 = client.post("/api/v1/members", json={"name": "Bob", "email": "bob@example.com"}).json()

    client.post("/api/v1/borrows", json={"book_id": book["id"], "member_id": m1["id"]})
    resp = client.post("/api/v1/borrows", json={"book_id": book["id"], "member_id": m2["id"]})
    assert resp.status_code == 409


def test_return_book(client):
    book = client.post("/api/v1/books", json={"title": "SICP", "author": "Abelson"}).json()
    member = client.post(
        "/api/v1/members", json={"name": "Alice", "email": "alice@example.com"}
    ).json()
    borrow = client.post(
        "/api/v1/borrows", json={"book_id": book["id"], "member_id": member["id"]}
    ).json()

    resp = client.patch(f"/api/v1/borrows/{borrow['id']}/return")
    assert resp.status_code == 200
    data = resp.json()
    assert data["returned_at"] is not None


def test_list_overdue(client, db_session):
    book = client.post("/api/v1/books", json={"title": "Late Book", "author": "Author"}).json()
    member = client.post(
        "/api/v1/members", json={"name": "Late Larry", "email": "late@example.com"}
    ).json()
    client.post("/api/v1/borrows", json={"book_id": book["id"], "member_id": member["id"]})

    # Set due_date to past to make it overdue
    record = db_session.query(Borrow).first()
    record.due_date = datetime.now(UTC) - timedelta(days=1)
    db_session.commit()

    resp = client.get("/api/v1/borrows?overdue=true")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] >= 1
    assert all(item["returned_at"] is None for item in data["items"])


def test_put_book(client):
    book = client.post("/api/v1/books", json={"title": "Old Title", "author": "Old Author"}).json()
    resp = client.put(
        f"/api/v1/books/{book['id']}",
        json={"title": "New Title", "author": "New Author", "genre": "Fiction"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["title"] == "New Title"
    assert data["author"] == "New Author"
    assert data["genre"] == "Fiction"


def test_patch_book(client):
    book = client.post(
        "/api/v1/books", json={"title": "Original", "author": "Author", "genre": "Sci-Fi"}
    ).json()
    resp = client.patch(f"/api/v1/books/{book['id']}", json={"title": "Updated Title"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["title"] == "Updated Title"
    assert data["author"] == "Author"
    assert data["genre"] == "Sci-Fi"


def test_put_book_not_found(client):
    import uuid_utils

    fake_id = str(uuid_utils.uuid7())
    resp = client.put(f"/api/v1/books/{fake_id}", json={"title": "X", "author": "Y"})
    assert resp.status_code == 404


def test_put_member(client):
    member = client.post(
        "/api/v1/members", json={"name": "Old Name", "email": "old@example.com"}
    ).json()
    resp = client.put(
        f"/api/v1/members/{member['id']}",
        json={"name": "New Name", "email": "new@example.com", "phone": "555-1234"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["name"] == "New Name"
    assert data["email"] == "new@example.com"
    assert data["phone"] == "555-1234"


def test_patch_member(client):
    member = client.post(
        "/api/v1/members", json={"name": "Alice", "email": "alice@example.com", "phone": "555-0000"}
    ).json()
    resp = client.patch(f"/api/v1/members/{member['id']}", json={"phone": "555-9999"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["phone"] == "555-9999"
    assert data["name"] == "Alice"
    assert data["email"] == "alice@example.com"


def test_patch_member_duplicate_email(client):
    client.post("/api/v1/members", json={"name": "Alice", "email": "alice@example.com"})
    bob = client.post("/api/v1/members", json={"name": "Bob", "email": "bob@example.com"}).json()
    resp = client.patch(f"/api/v1/members/{bob['id']}", json={"email": "alice@example.com"})
    assert resp.status_code == 409


def test_put_member_duplicate_email(client):
    client.post("/api/v1/members", json={"name": "Alice", "email": "alice@example.com"})
    bob = client.post("/api/v1/members", json={"name": "Bob", "email": "bob@example.com"}).json()
    resp = client.put(
        f"/api/v1/members/{bob['id']}",
        json={"name": "Bob Updated", "email": "alice@example.com"},
    )
    assert resp.status_code == 409


# --- ISBN uniqueness ---

def test_create_book_duplicate_isbn(client):
    client.post("/api/v1/books", json={"title": "Book A", "author": "Author", "isbn": "9781234567890"})
    resp = client.post("/api/v1/books", json={"title": "Book B", "author": "Author", "isbn": "9781234567890"})
    assert resp.status_code == 409
    assert "9781234567890" in resp.json()["detail"]["message"]


def test_patch_book_duplicate_isbn(client):
    client.post("/api/v1/books", json={"title": "Book A", "author": "Author", "isbn": "9781234567890"})
    book_b = client.post("/api/v1/books", json={"title": "Book B", "author": "Author", "isbn": "9780000000000"}).json()
    resp = client.patch(f"/api/v1/books/{book_b['id']}", json={"isbn": "9781234567890"})
    assert resp.status_code == 409
    assert "9781234567890" in resp.json()["detail"]["message"]


def test_create_book_same_isbn_allowed_for_same_book(client):
    book = client.post("/api/v1/books", json={"title": "Book A", "author": "Author", "isbn": "9781234567890"}).json()
    resp = client.patch(f"/api/v1/books/{book['id']}", json={"isbn": "9781234567890"})
    assert resp.status_code == 200


# --- Phone validation ---

def test_create_member_invalid_phone(client):
    resp = client.post(
        "/api/v1/members",
        json={"name": "Alice", "email": "alice@example.com", "phone": "call me maybe"},
    )
    assert resp.status_code == 422
    detail = resp.json()["detail"]
    assert detail["code"] == "ValidationError"
    assert "phone" in detail["message"].lower()


def test_create_member_valid_phone_formats(client):
    for i, phone in enumerate(["+1 (555) 123-4567", "555-123-4567", "+919876543210", "(555) 123.4567"]):
        resp = client.post(
            "/api/v1/members",
            json={"name": f"User {i}", "email": f"user{i}@example.com", "phone": phone},
        )
        assert resp.status_code == 201, f"Expected 201 for phone={phone}, got {resp.status_code}"


def test_patch_member_invalid_phone(client):
    member = client.post("/api/v1/members", json={"name": "Alice", "email": "alice@example.com"}).json()
    resp = client.patch(f"/api/v1/members/{member['id']}", json={"phone": "not a phone"})
    assert resp.status_code == 422
    assert resp.json()["detail"]["code"] == "ValidationError"


def test_create_member_null_phone_allowed(client):
    resp = client.post("/api/v1/members", json={"name": "Alice", "email": "alice@example.com"})
    assert resp.status_code == 201
    assert resp.json()["phone"] is None


# --- Email validation ---

def test_create_member_invalid_email(client):
    resp = client.post(
        "/api/v1/members",
        json={"name": "Alice", "email": "not-an-email"},
    )
    assert resp.status_code == 422
    detail = resp.json()["detail"]
    assert detail["code"] == "ValidationError"
    assert "email" in detail["message"].lower()


def test_create_member_valid_email_formats(client):
    for i, email in enumerate(["user@example.com", "user+tag@sub.domain.org", "x@y.co"]):
        resp = client.post("/api/v1/members", json={"name": f"User {i}", "email": email})
        assert resp.status_code == 201, f"Expected 201 for email={email}, got {resp.status_code}"


def test_patch_member_invalid_email(client):
    member = client.post("/api/v1/members", json={"name": "Alice", "email": "alice@example.com"}).json()
    resp = client.patch(f"/api/v1/members/{member['id']}", json={"email": "plaintext"})
    assert resp.status_code == 422
    assert resp.json()["detail"]["code"] == "ValidationError"


# --- 422 error shape ---

def test_422_error_shape(client):
    resp = client.post("/api/v1/members", json={"name": "Alice"})  # missing email
    assert resp.status_code == 422
    detail = resp.json()["detail"]
    assert "code" in detail
    assert "message" in detail
    assert detail["code"] == "ValidationError"


def test_filter_by_member(client):
    book1 = client.post("/api/v1/books", json={"title": "Book 1", "author": "Author"}).json()
    book2 = client.post("/api/v1/books", json={"title": "Book 2", "author": "Author"}).json()
    m1 = client.post(
        "/api/v1/members", json={"name": "Member One", "email": "m1@example.com"}
    ).json()
    m2 = client.post(
        "/api/v1/members", json={"name": "Member Two", "email": "m2@example.com"}
    ).json()

    client.post("/api/v1/borrows", json={"book_id": book1["id"], "member_id": m1["id"]})
    client.post("/api/v1/borrows", json={"book_id": book2["id"], "member_id": m2["id"]})

    resp = client.get(f"/api/v1/borrows?member_id={m1['id']}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 1
    assert data["items"][0]["member_id"] == m1["id"]
