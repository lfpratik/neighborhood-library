"use client";

import { useState } from "react";
import { toast } from "sonner";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { updateBookStatus } from "@/lib/api";
import { getStatusColor } from "@/lib/utils";
import type { Book } from "@/types";

interface Props {
  books: Book[];
  onRefresh: () => void;
}

export default function BookTable({ books, onRefresh }: Props) {
  const [retiring, setRetiring] = useState<string | null>(null);

  async function handleRetire(book: Book) {
    setRetiring(book.id);
    try {
      await updateBookStatus(book.id, "retired");
      toast.success(`"${book.title}" retired`);
      onRefresh();
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Failed to retire book");
    } finally {
      setRetiring(null);
    }
  }

  if (books.length === 0) {
    return (
      <div className="rounded-md border border-stone-200 bg-white px-6 py-12 text-center">
        <p className="text-sm text-stone-400">No books found</p>
      </div>
    );
  }

  return (
    <div className="rounded-md border border-stone-200 bg-white">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Title</TableHead>
            <TableHead>Author</TableHead>
            <TableHead>ISBN</TableHead>
            <TableHead>Genre</TableHead>
            <TableHead>Status</TableHead>
            <TableHead className="w-28">Actions</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {books.map((book) => (
            <TableRow key={book.id}>
              <TableCell className="font-medium text-stone-800">{book.title}</TableCell>
              <TableCell className="text-stone-600">{book.author}</TableCell>
              <TableCell className="text-stone-500">{book.isbn ?? "—"}</TableCell>
              <TableCell className="text-stone-500">{book.genre ?? "—"}</TableCell>
              <TableCell>
                <Badge variant={getStatusColor("book", book.status)} className="capitalize">
                  {book.status}
                </Badge>
              </TableCell>
              <TableCell>
                {book.status === "available" ? (
                  <Button
                    size="sm"
                    variant="destructive"
                    disabled={retiring === book.id}
                    onClick={() => handleRetire(book)}
                  >
                    {retiring === book.id ? "Retiring…" : "Retire"}
                  </Button>
                ) : (
                  <span className="text-sm capitalize text-stone-400">{book.status}</span>
                )}
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  );
}
