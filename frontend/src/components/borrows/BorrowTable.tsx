"use client";

import { useState } from "react";
import Link from "next/link";
import { Eye } from "lucide-react";
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
import { returnBorrow } from "@/lib/api";
import { getStatusColor, formatDate, isOverdue } from "@/lib/utils";
import type { BorrowSummary } from "@/types";

interface Props {
  borrows: BorrowSummary[];
  onRefresh: () => void;
}

function getBorrowStatus(borrow: BorrowSummary): "returned" | "overdue" | "active" {
  if (borrow.returned_at !== null) return "returned";
  if (isOverdue(borrow.due_date, borrow.returned_at)) return "overdue";
  return "active";
}

export default function BorrowTable({ borrows, onRefresh }: Props) {
  const [returning, setReturning] = useState<string | null>(null);

  async function handleReturn(borrow: BorrowSummary) {
    setReturning(borrow.id);
    try {
      await returnBorrow(borrow.id);
      toast.success("Book returned");
      onRefresh();
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Failed to return book");
    } finally {
      setReturning(null);
    }
  }

  if (borrows.length === 0) {
    return (
      <div className="rounded-md border border-stone-200 bg-white px-6 py-12 text-center">
        <p className="text-sm text-stone-400">No borrows found</p>
      </div>
    );
  }

  return (
    <div className="rounded-md border border-stone-200 bg-white">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Book Title</TableHead>
            <TableHead>Member Name</TableHead>
            <TableHead>Borrowed</TableHead>
            <TableHead>Due Date</TableHead>
            <TableHead>Status</TableHead>
            <TableHead className="w-48">Actions</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {borrows.map((borrow) => {
            const status = getBorrowStatus(borrow);
            return (
              <TableRow key={borrow.id} className={status === "overdue" ? "bg-red-50" : ""}>
                <TableCell className="font-medium">
                  <Link href={`/books/${borrow.book_id}`} className="text-blue-600 hover:underline">
                    {borrow.book_title}
                  </Link>
                </TableCell>
                <TableCell>
                  <Link href={`/members/${borrow.member_id}`} className="text-blue-600 hover:underline">
                    {borrow.member_name}
                  </Link>
                </TableCell>
                <TableCell className="text-stone-500">{formatDate(borrow.borrowed_at)}</TableCell>
                <TableCell className="text-stone-500">{formatDate(borrow.due_date)}</TableCell>
                <TableCell>
                  <Badge variant={getStatusColor("borrow", status)} className="capitalize">
                    {status}
                  </Badge>
                </TableCell>
                <TableCell>
                  <div className="flex items-center gap-2">
                    {status !== "returned" ? (
                      <Button
                        size="sm"
                        variant="outline"
                        disabled={returning === borrow.id}
                        onClick={() => handleReturn(borrow)}
                      >
                        {returning === borrow.id ? "Returning…" : "Return"}
                      </Button>
                    ) : (
                      <span className="text-sm text-stone-400">
                        {formatDate(borrow.returned_at!)}
                      </span>
                    )}
                    <Link href={`/borrows/${borrow.id}`}>
                      <Button size="sm" variant="ghost" className="p-1">
                        <Eye className="h-4 w-4 text-stone-500" />
                      </Button>
                    </Link>
                  </div>
                </TableCell>
              </TableRow>
            );
          })}
        </TableBody>
      </Table>
    </div>
  );
}
