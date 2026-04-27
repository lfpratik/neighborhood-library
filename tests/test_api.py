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
