"use client";

import { useEffect, useRef, useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import MemberTable from "@/components/members/MemberTable";
import MemberFormModal from "@/components/members/MemberFormModal";
import { getMembers } from "@/lib/api";
import { PAGE_SIZE } from "@/lib/constants";
import type { Member } from "@/types";
import { toast } from "sonner";

function SkeletonRows() {
  return (
    <div className="rounded-md border border-stone-200 bg-white divide-y divide-stone-100">
      {[0, 1, 2, 3, 4].map((i) => (
        <div key={i} className="flex gap-4 px-4 py-3">
          <div className="h-4 w-40 bg-stone-200 rounded animate-pulse" />
          <div className="h-4 w-48 bg-stone-200 rounded animate-pulse" />
          <div className="h-4 w-24 bg-stone-200 rounded animate-pulse" />
          <div className="h-4 w-16 bg-stone-200 rounded animate-pulse ml-auto" />
        </div>
      ))}
    </div>
  );
}

export default function MembersPage() {
  const [members, setMembers] = useState<Member[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState("all");
  const [loading, setLoading] = useState(true);
  const [modalOpen, setModalOpen] = useState(false);

  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const totalPages = Math.max(1, Math.ceil(total / PAGE_SIZE));

  function fetchMembers(p: number, q: string, status: string) {
    setLoading(true);
    getMembers({
      page: p,
      size: PAGE_SIZE,
      search: q || undefined,
      status: status === "all" ? undefined : status,
    })
      .then((res) => {
        setMembers(res.items);
        setTotal(res.total);
      })
      .catch((err: Error) => toast.error(err.message))
      .finally(() => setLoading(false));
  }

  useEffect(() => {
    fetchMembers(page, search, statusFilter);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [page, statusFilter]);

  function handleSearchChange(value: string) {
    setSearch(value);
    if (debounceRef.current) clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(() => {
      setPage(1);
      fetchMembers(1, value, statusFilter);
    }, 300);
  }

  function handleStatusChange(value: string | null) {
    setStatusFilter(value ?? "all");
    setPage(1);
  }

  function handleRefresh() {
    fetchMembers(page, search, statusFilter);
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-stone-800">Members</h1>
        <Button onClick={() => setModalOpen(true)}>Add Member</Button>
      </div>

      {/* Filters */}
      <div className="flex gap-3">
        <Input
          placeholder="Search name or email…"
          value={search}
          onChange={(e) => handleSearchChange(e.target.value)}
          className="max-w-xs bg-white"
        />
        <Select value={statusFilter} onValueChange={handleStatusChange}>
          <SelectTrigger className="w-40 bg-white">
            <SelectValue placeholder="All statuses" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All</SelectItem>
            <SelectItem value="active">Active</SelectItem>
            <SelectItem value="inactive">Inactive</SelectItem>
            <SelectItem value="suspended">Suspended</SelectItem>
          </SelectContent>
        </Select>
      </div>

      {/* Table */}
      {loading ? (
        <SkeletonRows />
      ) : (
        <MemberTable members={members} onRefresh={handleRefresh} />
      )}

      {/* Pagination */}
      <div className="flex items-center justify-between text-sm text-stone-500">
        <span>
          {total} {total === 1 ? "member" : "members"} total
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

      <MemberFormModal
        open={modalOpen}
        onOpenChange={setModalOpen}
        onSuccess={handleRefresh}
      />
    </div>
  );
}
