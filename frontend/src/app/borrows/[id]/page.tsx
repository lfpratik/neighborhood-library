"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { toast } from "sonner";
import Link from "next/link";
import { AlertTriangle } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import BackLink from "@/components/shared/BackLink";
import DetailField from "@/components/shared/DetailField";
import { getBorrow, returnBorrow } from "@/lib/api";
import { formatDate, formatDateTime, getStatusColor, isOverdue } from "@/lib/utils";
import type { Borrow } from "@/types";

function getBorrowStatus(borrow: Borrow): "returned" | "overdue" | "active" {
  if (borrow.returned_at !== null) return "returned";
  if (isOverdue(borrow.due_date, borrow.returned_at)) return "overdue";
  return "active";
}

function SkeletonCard() {
  return (
    <div className="space-y-6">
      <div className="h-4 w-32 bg-stone-200 rounded animate-pulse" />
      <div className="h-8 w-48 bg-stone-200 rounded animate-pulse" />
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

export default function BorrowDetailPage() {
  const { id } = useParams<{ id: string }>();
  const [borrow, setBorrow] = useState<Borrow | null>(null);
  const [loading, setLoading] = useState(true);
  const [notFound, setNotFound] = useState(false);
  const [returning, setReturning] = useState(false);

  function fetchBorrow() {
    setLoading(true);
    getBorrow(id)
      .then(setBorrow)
      .catch(() => setNotFound(true))
      .finally(() => setLoading(false));
  }

  useEffect(() => {
    fetchBorrow();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [id]);

  async function handleReturn() {
    if (!borrow) return;
    setReturning(true);
    try {
      await returnBorrow(borrow.id);
      toast.success("Book returned");
      fetchBorrow();
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Failed to return book");
    } finally {
      setReturning(false);
    }
  }

  if (loading) return <SkeletonCard />;

  if (notFound || !borrow) {
    return (
      <div className="space-y-4">
        <BackLink href="/borrows" label="Back to Borrows" />
        <p className="text-stone-500">Borrow not found.</p>
      </div>
    );
  }

  const borrowStatus = getBorrowStatus(borrow);
  const overduedays =
    borrowStatus === "overdue"
      ? Math.ceil((Date.now() - new Date(borrow.due_date).getTime()) / 86400000)
      : 0;

  return (
    <div className="space-y-6">
      <BackLink href="/borrows" label="Back to Borrows" />

      {/* Header */}
      <div className="flex items-center gap-3">
        <h1 className="text-2xl font-bold text-stone-800">Borrow Details</h1>
        <Badge variant={getStatusColor("borrow", borrowStatus)} className="capitalize">
          {borrowStatus}
        </Badge>
      </div>

      {/* Detail Card */}
      <Card>
        <CardContent className="pt-6">
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <DetailField
              label="Book"
              value={
                <Link href={`/books/${borrow.book_id}`} className="text-blue-600 hover:underline">
                  {borrow.book.title} by {borrow.book.author}
                </Link>
              }
            />
            <DetailField
              label="Member"
              value={
                <Link href={`/members/${borrow.member_id}`} className="text-blue-600 hover:underline">
                  {borrow.member.name} ({borrow.member.email})
                </Link>
              }
            />
            <DetailField label="Borrowed At" value={formatDateTime(borrow.borrowed_at)} />
            <DetailField label="Due Date" value={formatDateTime(borrow.due_date)} />
            <DetailField
              label="Returned At"
              value={
                borrow.returned_at ? (
                  formatDateTime(borrow.returned_at)
                ) : (
                  <span className="text-stone-400">Not yet returned</span>
                )
              }
            />
            <DetailField label="Notes" value={borrow.notes ?? "—"} />
            <DetailField label="Created" value={formatDate(borrow.created_at)} />
          </div>
        </CardContent>
      </Card>

      {/* Overdue alert */}
      {borrowStatus === "overdue" && (
        <div className="flex items-center gap-2 rounded-md border border-amber-300 bg-amber-50 px-4 py-3 text-amber-800">
          <AlertTriangle className="h-4 w-4 shrink-0" />
          <span className="text-sm font-medium">
            This book is {overduedays} {overduedays === 1 ? "day" : "days"} overdue
          </span>
        </div>
      )}

      {/* Action */}
      <div>
        {(borrowStatus === "active" || borrowStatus === "overdue") && (
          <Button onClick={handleReturn} disabled={returning}>
            {returning ? "Returning…" : "Return Book"}
          </Button>
        )}
        {borrowStatus === "returned" && borrow.returned_at && (
          <p className="text-sm text-green-600">
            Returned on {formatDate(borrow.returned_at)}
          </p>
        )}
      </div>
    </div>
  );
}
