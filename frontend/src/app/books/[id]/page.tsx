"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { toast } from "sonner";
import Link from "next/link";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import BackLink from "@/components/shared/BackLink";
import DetailField from "@/components/shared/DetailField";
import { getBook, updateBook, updateBookStatus, getBorrows } from "@/lib/api";
import {
  formatDate,
  formatDateTime,
  getStatusColor,
  isOverdue,
} from "@/lib/utils";
import type { Book, Borrow } from "@/types";

function getBorrowStatus(borrow: Borrow): "returned" | "overdue" | "active" {
  if (borrow.returned_at !== null) return "returned";
  if (isOverdue(borrow.due_date, borrow.returned_at)) return "overdue";
  return "active";
}

function SkeletonCard() {
  return (
    <div className="space-y-6">
      <div className="h-4 w-32 bg-stone-200 rounded animate-pulse" />
      <div className="h-8 w-64 bg-stone-200 rounded animate-pulse" />
      <div className="rounded-lg border border-stone-200 bg-white p-6 space-y-4">
        {[0, 1, 2, 3, 4, 5].map((i) => (
          <div key={i} className="space-y-1">
            <div className="h-3 w-20 bg-stone-200 rounded animate-pulse" />
            <div className="h-4 w-48 bg-stone-200 rounded animate-pulse" />
          </div>
        ))}
      </div>
    </div>
  );
}

export default function BookDetailPage() {
  const { id } = useParams<{ id: string }>();
  const [book, setBook] = useState<Book | null>(null);
  const [borrows, setBorrows] = useState<Borrow[]>([]);
  const [loading, setLoading] = useState(true);
  const [notFound, setNotFound] = useState(false);
  const [editMode, setEditMode] = useState(false);
  const [saving, setSaving] = useState(false);
  const [retiring, setRetiring] = useState(false);

  const [form, setForm] = useState({
    title: "",
    author: "",
    isbn: "",
    publisher: "",
    publication_year: "",
    genre: "",
  });

  function fetchBook() {
    setLoading(true);
    getBook(id)
      .then((b) => {
        setBook(b);
        setForm({
          title: b.title,
          author: b.author,
          isbn: b.isbn ?? "",
          publisher: b.publisher ?? "",
          publication_year:
            b.publication_year != null ? String(b.publication_year) : "",
          genre: b.genre ?? "",
        });
      })
      .catch(() => setNotFound(true))
      .finally(() => setLoading(false));
  }

  function fetchBorrows() {
    getBorrows({ book_id: id, size: 50 }).then((res) => setBorrows(res.items));
  }

  useEffect(() => {
    fetchBook();
    fetchBorrows();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [id]);

  async function handleSave() {
    if (!book) return;
    const changed: Record<string, string | number | null> = {};
    if (form.title !== book.title) changed.title = form.title;
    if (form.author !== book.author) changed.author = form.author;
    const isbn = form.isbn.trim() || null;
    if (isbn !== book.isbn) changed.isbn = isbn;
    const publisher = form.publisher.trim() || null;
    if (publisher !== book.publisher) changed.publisher = publisher;
    const year = form.publication_year
      ? parseInt(form.publication_year, 10)
      : null;
    if (year !== book.publication_year) changed.publication_year = year;
    const genre = form.genre.trim() || null;
    if (genre !== book.genre) changed.genre = genre;

    if (Object.keys(changed).length === 0) {
      setEditMode(false);
      return;
    }

    setSaving(true);
    try {
      await updateBook(id, changed);
      toast.success("Book updated");
      setEditMode(false);
      fetchBook();
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Failed to update book");
    } finally {
      setSaving(false);
    }
  }

  async function handleRetire() {
    if (!book) return;
    setRetiring(true);
    try {
      await updateBookStatus(book.id, "retired");
      toast.success("Book retired");
      fetchBook();
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Failed to retire book");
    } finally {
      setRetiring(false);
    }
  }

  function handleCancelEdit() {
    if (!book) return;
    setForm({
      title: book.title,
      author: book.author,
      isbn: book.isbn ?? "",
      publisher: book.publisher ?? "",
      publication_year:
        book.publication_year != null ? String(book.publication_year) : "",
      genre: book.genre ?? "",
    });
    setEditMode(false);
  }

  if (loading) return <SkeletonCard />;

  if (notFound || !book) {
    return (
      <div className="space-y-4">
        <BackLink href="/books" label="Back to Books" />
        <p className="text-stone-500">Book not found.</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <BackLink href="/books" label="Back to Books" />

      {/* Header */}
      <div className="flex items-start justify-between gap-4">
        <div className="flex items-center gap-3">
          <h1 className="text-2xl font-bold text-stone-800">{book.title}</h1>
          <Badge
            variant={getStatusColor("book", book.status)}
            className="capitalize"
          >
            {book.status}
          </Badge>
        </div>
        {!editMode && (
          <Button variant="outline" onClick={() => setEditMode(true)}>
            Edit
          </Button>
        )}
      </div>

      {/* Detail Card */}
      <Card>
        <CardContent className="pt-6">
          {editMode ? (
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
              <div className="space-y-1">
                <p className="text-sm text-muted-foreground">Title</p>
                <Input
                  value={form.title}
                  onChange={(e) =>
                    setForm((f) => ({ ...f, title: e.target.value }))
                  }
                />
              </div>
              <div className="space-y-1">
                <p className="text-sm text-muted-foreground">Author</p>
                <Input
                  value={form.author}
                  onChange={(e) =>
                    setForm((f) => ({ ...f, author: e.target.value }))
                  }
                />
              </div>
              <div className="space-y-1">
                <p className="text-sm text-muted-foreground">ISBN</p>
                <Input
                  value={form.isbn}
                  onChange={(e) =>
                    setForm((f) => ({ ...f, isbn: e.target.value }))
                  }
                  placeholder="—"
                />
              </div>
              <div className="space-y-1">
                <p className="text-sm text-muted-foreground">Publisher</p>
                <Input
                  value={form.publisher}
                  onChange={(e) =>
                    setForm((f) => ({ ...f, publisher: e.target.value }))
                  }
                  placeholder="—"
                />
              </div>
              <div className="space-y-1">
                <p className="text-sm text-muted-foreground">
                  Publication Year
                </p>
                <Input
                  type="number"
                  value={form.publication_year}
                  onChange={(e) =>
                    setForm((f) => ({ ...f, publication_year: e.target.value }))
                  }
                  placeholder="—"
                />
              </div>
              <div className="space-y-1">
                <p className="text-sm text-muted-foreground">Genre</p>
                <Input
                  value={form.genre}
                  onChange={(e) =>
                    setForm((f) => ({ ...f, genre: e.target.value }))
                  }
                  placeholder="—"
                />
              </div>
              <DetailField
                label="Status"
                value={
                  <Badge
                    variant={getStatusColor("book", book.status)}
                    className="capitalize"
                  >
                    {book.status}
                  </Badge>
                }
              />
              <DetailField
                label="Created"
                value={formatDate(book.created_at)}
              />
              <DetailField
                label="Last Updated"
                value={formatDate(book.updated_at)}
              />
            </div>
          ) : (
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
              <DetailField label="Title" value={book.title} />
              <DetailField label="Author" value={book.author} />
              <DetailField label="ISBN" value={book.isbn ?? "—"} />
              <DetailField label="Publisher" value={book.publisher ?? "—"} />
              <DetailField
                label="Publication Year"
                value={
                  book.publication_year != null
                    ? String(book.publication_year)
                    : "—"
                }
              />
              <DetailField label="Genre" value={book.genre ?? "—"} />
              <DetailField
                label="Status"
                value={
                  <Badge
                    variant={getStatusColor("book", book.status)}
                    className="capitalize"
                  >
                    {book.status}
                  </Badge>
                }
              />
              <DetailField
                label="Created"
                value={formatDate(book.created_at)}
              />
              <DetailField
                label="Last Updated"
                value={formatDate(book.updated_at)}
              />
            </div>
          )}
        </CardContent>
      </Card>

      {/* Edit actions */}
      {editMode && (
        <div className="flex gap-2">
          <Button onClick={handleSave} disabled={saving}>
            {saving ? "Saving…" : "Save"}
          </Button>
          <Button
            variant="outline"
            onClick={handleCancelEdit}
            disabled={saving}
          >
            Cancel
          </Button>
        </div>
      )}

      {/* Status actions */}
      {!editMode && (
        <div>
          {book.status === "available" && (
            <Button
              variant="destructive"
              onClick={handleRetire}
              disabled={retiring}
            >
              {retiring ? "Retiring…" : "Retire Book"}
            </Button>
          )}
          {book.status === "borrowed" && (
            <p className="text-sm text-stone-500">Currently Borrowed</p>
          )}
          {book.status === "retired" && (
            <p className="text-sm text-stone-500">This book is retired</p>
          )}
        </div>
      )}

      {/* Borrow History */}
      <div className="space-y-3">
        <h2 className="text-lg font-semibold text-stone-800">Borrow History</h2>
        {borrows.length === 0 ? (
          <p className="text-sm text-stone-400">No borrow history</p>
        ) : (
          <div className="rounded-md border border-stone-200 bg-white">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Member</TableHead>
                  <TableHead>Borrowed</TableHead>
                  <TableHead>Due Date</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Returned</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {borrows.map((borrow) => {
                  const borrowStatus = getBorrowStatus(borrow);
                  return (
                    <TableRow key={borrow.id}>
                      <TableCell>
                        <Link
                          href={`/members/${borrow.member_id}`}
                          className="text-blue-600 hover:underline"
                        >
                          {borrow.member.name}
                        </Link>
                      </TableCell>
                      <TableCell className="text-stone-500">
                        {formatDate(borrow.borrowed_at)}
                      </TableCell>
                      <TableCell className="text-stone-500">
                        {formatDate(borrow.due_date)}
                      </TableCell>
                      <TableCell>
                        <Badge
                          variant={getStatusColor("borrow", borrowStatus)}
                          className="capitalize"
                        >
                          {borrowStatus}
                        </Badge>
                      </TableCell>
                      <TableCell className="text-stone-500">
                        {borrow.returned_at
                          ? formatDate(borrow.returned_at)
                          : "—"}
                      </TableCell>
                    </TableRow>
                  );
                })}
              </TableBody>
            </Table>
          </div>
        )}
      </div>
    </div>
  );
}
