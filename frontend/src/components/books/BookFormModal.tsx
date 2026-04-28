"use client";

import { useState } from "react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { createBook } from "@/lib/api";

interface Props {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onSuccess: () => void;
}

interface FormState {
  title: string;
  author: string;
  isbn: string;
  publisher: string;
  publication_year: string;
  genre: string;
}

const empty: FormState = {
  title: "",
  author: "",
  isbn: "",
  publisher: "",
  publication_year: "",
  genre: "",
};

export default function BookFormModal({ open, onOpenChange, onSuccess }: Props) {
  const [form, setForm] = useState<FormState>(empty);
  const [errors, setErrors] = useState<Partial<FormState>>({});
  const [submitting, setSubmitting] = useState(false);

  function set(field: keyof FormState, value: string) {
    setForm((f) => ({ ...f, [field]: value }));
    setErrors((e) => ({ ...e, [field]: undefined }));
  }

  function validate(): boolean {
    const errs: Partial<FormState> = {};
    if (!form.title.trim()) errs.title = "Title is required";
    if (!form.author.trim()) errs.author = "Author is required";
    setErrors(errs);
    return Object.keys(errs).length === 0;
  }

  async function handleSubmit() {
    if (!validate()) return;
    setSubmitting(true);
    try {
      await createBook({
        title: form.title.trim(),
        author: form.author.trim(),
        isbn: form.isbn.trim() || undefined,
        publisher: form.publisher.trim() || undefined,
        publication_year: form.publication_year ? Number(form.publication_year) : undefined,
        genre: form.genre.trim() || undefined,
      });
      toast.success("Book added");
      setForm(empty);
      onSuccess();
      onOpenChange(false);
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Failed to add book");
    } finally {
      setSubmitting(false);
    }
  }

  function handleOpenChange(val: boolean) {
    if (!val) setForm(empty);
    setErrors({});
    onOpenChange(val);
  }

  return (
    <Dialog open={open} onOpenChange={handleOpenChange}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>Add Book</DialogTitle>
        </DialogHeader>
        <div className="space-y-4 py-2">
          <Field label="Title *" error={errors.title}>
            <Input
              placeholder="e.g. Clean Code"
              value={form.title}
              onChange={(e) => set("title", e.target.value)}
            />
          </Field>
          <Field label="Author *" error={errors.author}>
            <Input
              placeholder="e.g. Robert C. Martin"
              value={form.author}
              onChange={(e) => set("author", e.target.value)}
            />
          </Field>
          <div className="grid grid-cols-2 gap-4">
            <Field label="ISBN">
              <Input
                placeholder="978-..."
                value={form.isbn}
                onChange={(e) => set("isbn", e.target.value)}
              />
            </Field>
            <Field label="Publication Year">
              <Input
                type="number"
                placeholder="2024"
                value={form.publication_year}
                onChange={(e) => set("publication_year", e.target.value)}
              />
            </Field>
          </div>
          <Field label="Publisher">
            <Input
              placeholder="e.g. O'Reilly"
              value={form.publisher}
              onChange={(e) => set("publisher", e.target.value)}
            />
          </Field>
          <Field label="Genre">
            <Input
              placeholder="e.g. Technology"
              value={form.genre}
              onChange={(e) => set("genre", e.target.value)}
            />
          </Field>
        </div>
        <DialogFooter>
          <Button variant="outline" onClick={() => handleOpenChange(false)} disabled={submitting}>
            Cancel
          </Button>
          <Button onClick={handleSubmit} disabled={submitting}>
            {submitting ? "Adding…" : "Add Book"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

function Field({
  label,
  error,
  children,
}: {
  label: string;
  error?: string;
  children: React.ReactNode;
}) {
  return (
    <div className="space-y-1">
      <label className="text-sm font-medium text-stone-700">{label}</label>
      {children}
      {error && <p className="text-xs text-red-500">{error}</p>}
    </div>
  );
}
