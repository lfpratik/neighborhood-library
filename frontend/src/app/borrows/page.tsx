"use client";

import { useEffect, useState } from "react";
import { Button } from "@/components/ui/button";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import BorrowTable from "@/components/borrows/BorrowTable";
import BorrowFormModal from "@/components/borrows/BorrowFormModal";
import { getBorrows } from "@/lib/api";
import { PAGE_SIZE } from "@/lib/constants";
import type { BorrowSummary } from "@/types";
import { toast } from "sonner";

type TabValue = "all" | "active" | "overdue" | "returned";

function tabToParams(
  tab: TabValue,
): Partial<{ active: boolean; overdue: boolean }> {
  if (tab === "active") return { active: true };
  if (tab === "overdue") return { overdue: true };
  if (tab === "returned") return { active: false };
  return {};
}

function SkeletonRows() {
  return (
    <div className="rounded-md border border-stone-200 bg-white divide-y divide-stone-100">
      {[0, 1, 2, 3, 4].map((i) => (
        <div key={i} className="flex gap-4 px-4 py-3">
          <div className="h-4 w-40 bg-stone-200 rounded animate-pulse" />
          <div className="h-4 w-32 bg-stone-200 rounded animate-pulse" />
          <div className="h-4 w-24 bg-stone-200 rounded animate-pulse" />
          <div className="h-4 w-24 bg-stone-200 rounded animate-pulse" />
          <div className="h-4 w-16 bg-stone-200 rounded animate-pulse ml-auto" />
        </div>
      ))}
    </div>
  );
}

export default function BorrowsPage() {
  const [borrows, setBorrows] = useState<BorrowSummary[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [activeTab, setActiveTab] = useState<TabValue>("all");
  const [loading, setLoading] = useState(true);
  const [modalOpen, setModalOpen] = useState(false);

  const totalPages = Math.max(1, Math.ceil(total / PAGE_SIZE));

  function fetchBorrows(p: number, tab: TabValue) {
    setLoading(true);
    getBorrows({ page: p, size: PAGE_SIZE, ...tabToParams(tab) })
      .then((res) => {
        setBorrows(res.items);
        setTotal(res.total);
      })
      .catch((err: Error) => toast.error(err.message))
      .finally(() => setLoading(false));
  }

  useEffect(() => {
    fetchBorrows(page, activeTab);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [page, activeTab]);

  function handleTabChange(value: string) {
    setActiveTab(value as TabValue);
    setPage(1);
  }

  function handleRefresh() {
    fetchBorrows(page, activeTab);
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-stone-800">Borrows</h1>
        <Button onClick={() => setModalOpen(true)}>Borrow Book</Button>
      </div>

      {/* Tabs */}
      <Tabs value={activeTab} onValueChange={handleTabChange}>
        <TabsList>
          <TabsTrigger value="all">All</TabsTrigger>
          <TabsTrigger value="active">Active</TabsTrigger>
          <TabsTrigger value="overdue">Overdue</TabsTrigger>
          <TabsTrigger value="returned">Returned</TabsTrigger>
        </TabsList>
      </Tabs>

      {/* Table */}
      {loading ? (
        <SkeletonRows />
      ) : (
        <BorrowTable borrows={borrows} onRefresh={handleRefresh} />
      )}

      {/* Pagination */}
      <div className="flex items-center justify-between text-sm text-stone-500">
        <span>
          {total} {total === 1 ? "borrow" : "borrows"} total
        </span>
        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            disabled={page <= 1}
            onClick={() => setPage((p) => p - 1)}
          >
            Previous
          </Button>
          <span>
            Page {page} of {totalPages}
          </span>
          <Button
            variant="outline"
            size="sm"
            disabled={page >= totalPages}
            onClick={() => setPage((p) => p + 1)}
          >
            Next
          </Button>
        </div>
      </div>

      <BorrowFormModal
        open={modalOpen}
        onOpenChange={setModalOpen}
        onSuccess={handleRefresh}
      />
    </div>
  );
}
