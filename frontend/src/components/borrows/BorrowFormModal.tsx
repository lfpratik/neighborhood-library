"use client";

import { useEffect, useState } from "react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "@/components/ui/dialog";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { getBooks, getMembers, createBorrow } from "@/lib/api";
import type { Book, Member } from "@/types";

interface Props {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onSuccess: () => void;
}

export default function BorrowFormModal({ open, onOpenChange, onSuccess }: Props) {
  const [books, setBooks] = useState<Book[]>([]);
  const [members, setMembers] = useState<Member[]>([]);
  const [bookId, setBookId] = useState("");
  const [memberId, setMemberId] = useState("");
  const [notes, setNotes] = useState("");
  const [errors, setErrors] = useState<{ book?: string; member?: string }>({});
  const [submitting, setSubmitting] = useState(false);
  const [loadingOptions, setLoadingOptions] = useState(false);

  useEffect(() => {
    if (!open) return;
    setLoadingOptions(true);
    Promise.all([
      getBooks({ status: "available", size: 100 }),
      getMembers({ status: "active", size: 100 }),
    ])
      .then(([booksRes, membersRes]) => {
        setBooks(booksRes.items);
        setMembers(membersRes.items);
      })
      .finally(() => setLoadingOptions(false));
  }, [open]);

  function validate(): boolean {
    const errs: { book?: string; member?: string } = {};
    if (!bookId) errs.book = "Please select a book";
    if (!memberId) errs.member = "Please select a member";
    setErrors(errs);
    return Object.keys(errs).length === 0;
  }

  async function handleSubmit() {
    if (!validate()) return;
    setSubmitting(true);
    try {
      await createBorrow({
        book_id: bookId,
        member_id: memberId,
        notes: notes.trim() || undefined,
      });
      toast.success("Book borrowed successfully");
      handleOpenChange(false);
      onSuccess();
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Failed to borrow book");
    } finally {
      setSubmitting(false);
    }
  }

  function handleOpenChange(val: boolean) {
    if (!val) {
      setBookId("");
      setMemberId("");
      setNotes("");
      setErrors({});
    }
    onOpenChange(val);
  }

  return (
    <Dialog open={open} onOpenChange={handleOpenChange}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>Borrow Book</DialogTitle>
        </DialogHeader>
        <div className="space-y-4 py-2">
          <div className="space-y-1">
            <label className="text-sm font-medium text-stone-700">Book *</label>
            <Select
              value={bookId}
              onValueChange={(v) => {
                setBookId(v ?? "");
                setErrors((e) => ({ ...e, book: undefined }));
              }}
              disabled={loadingOptions}
            >
              <SelectTrigger className="w-full">
                <SelectValue placeholder={loadingOptions ? "Loading…" : "Select a book"} />
              </SelectTrigger>
              <SelectContent>
                {books.map((book) => (
                  <SelectItem key={book.id} value={book.id}>
                    {book.title} — {book.author}
                  </SelectItem>
                ))}
                {!loadingOptions && books.length === 0 && (
                  <SelectItem value="__none__" disabled>
                    No available books
                  </SelectItem>
                )}
              </SelectContent>
            </Select>
            {errors.book && <p className="text-xs text-red-500">{errors.book}</p>}
          </div>

          <div className="space-y-1">
            <label className="text-sm font-medium text-stone-700">Member *</label>
            <Select
              value={memberId}
              onValueChange={(v) => {
                setMemberId(v ?? "");
                setErrors((e) => ({ ...e, member: undefined }));
              }}
              disabled={loadingOptions}
            >
              <SelectTrigger className="w-full">
                <SelectValue placeholder={loadingOptions ? "Loading…" : "Select a member"} />
              </SelectTrigger>
              <SelectContent>
                {members.map((member) => (
                  <SelectItem key={member.id} value={member.id}>
                    {member.name} ({member.email})
                  </SelectItem>
                ))}
                {!loadingOptions && members.length === 0 && (
                  <SelectItem value="__none__" disabled>
                    No active members
                  </SelectItem>
                )}
              </SelectContent>
            </Select>
            {errors.member && <p className="text-xs text-red-500">{errors.member}</p>}
          </div>

          <div className="space-y-1">
            <label className="text-sm font-medium text-stone-700">Notes</label>
            <textarea
              placeholder="Optional notes…"
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              rows={2}
              className="w-full rounded-md border border-input bg-transparent px-3 py-2 text-sm outline-none placeholder:text-muted-foreground focus-visible:border-ring focus-visible:ring-3 focus-visible:ring-ring/50 resize-none"
            />
          </div>
        </div>
        <DialogFooter>
          <Button variant="outline" onClick={() => handleOpenChange(false)} disabled={submitting}>
            Cancel
          </Button>
          <Button onClick={handleSubmit} disabled={submitting || loadingOptions}>
            {submitting ? "Borrowing…" : "Borrow Book"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
