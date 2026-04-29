"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { toast } from "sonner";
import Link from "next/link";
import { Card, CardContent } from "@/components/ui/card";
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
import { getMember, patchMember, updateMemberStatus, getBorrows } from "@/lib/api";
import { formatDate, getStatusColor, isOverdue } from "@/lib/utils";
import type { Member, Borrow } from "@/types";

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
        {[0, 1, 2, 3, 4].map((i) => (
          <div key={i} className="space-y-1">
            <div className="h-3 w-20 bg-stone-200 rounded animate-pulse" />
            <div className="h-4 w-48 bg-stone-200 rounded animate-pulse" />
          </div>
        ))}
      </div>
    </div>
  );
}

export default function MemberDetailPage() {
  const { id } = useParams<{ id: string }>();
  const [member, setMember] = useState<Member | null>(null);
  const [activeBorrows, setActiveBorrows] = useState<Borrow[]>([]);
  const [allBorrows, setAllBorrows] = useState<Borrow[]>([]);
  const [loading, setLoading] = useState(true);
  const [notFound, setNotFound] = useState(false);
  const [editMode, setEditMode] = useState(false);
  const [saving, setSaving] = useState(false);
  const [updatingStatus, setUpdatingStatus] = useState(false);

  const [form, setForm] = useState({
    name: "",
    email: "",
    phone: "",
    address: "",
  });

  function fetchMember() {
    setLoading(true);
    getMember(id)
      .then((m) => {
        setMember(m);
        setForm({
          name: m.name,
          email: m.email,
          phone: m.phone ?? "",
          address: m.address ?? "",
        });
      })
      .catch(() => setNotFound(true))
      .finally(() => setLoading(false));
  }

  function fetchBorrows() {
    getBorrows({ member_id: id, active: true, size: 50 }).then((res) =>
      setActiveBorrows(res.items)
    );
    getBorrows({ member_id: id, size: 50 }).then((res) => setAllBorrows(res.items));
  }

  useEffect(() => {
    fetchMember();
    fetchBorrows();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [id]);

  async function handleSave() {
    if (!member) return;
    const changed: Record<string, string | null> = {};
    if (form.name !== member.name) changed.name = form.name;
    if (form.email !== member.email) changed.email = form.email;
    const phone = form.phone.trim() || null;
    if (phone !== member.phone) changed.phone = phone;
    const address = form.address.trim() || null;
    if (address !== member.address) changed.address = address;

    if (Object.keys(changed).length === 0) {
      setEditMode(false);
      return;
    }

    setSaving(true);
    try {
      await patchMember(id, changed);
      toast.success("Member updated");
      setEditMode(false);
      fetchMember();
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Failed to update member");
    } finally {
      setSaving(false);
    }
  }

  async function handleStatusChange(newStatus: Member["status"]) {
    if (!member) return;
    setUpdatingStatus(true);
    try {
      await updateMemberStatus(member.id, newStatus);
      toast.success(`Member ${newStatus}`);
      fetchMember();
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Failed to update status");
    } finally {
      setUpdatingStatus(false);
    }
  }

  function handleCancelEdit() {
    if (!member) return;
    setForm({
      name: member.name,
      email: member.email,
      phone: member.phone ?? "",
      address: member.address ?? "",
    });
    setEditMode(false);
  }

  if (loading) return <SkeletonCard />;

  if (notFound || !member) {
    return (
      <div className="space-y-4">
        <BackLink href="/members" label="Back to Members" />
        <p className="text-stone-500">Member not found.</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <BackLink href="/members" label="Back to Members" />

      {/* Header */}
      <div className="flex items-start justify-between gap-4">
        <div className="flex items-center gap-3">
          <h1 className="text-2xl font-bold text-stone-800">{member.name}</h1>
          <Badge variant={getStatusColor("member", member.status)} className="capitalize">
            {member.status}
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
                <p className="text-sm text-muted-foreground">Name</p>
                <Input
                  value={form.name}
                  onChange={(e) => setForm((f) => ({ ...f, name: e.target.value }))}
                />
              </div>
              <div className="space-y-1">
                <p className="text-sm text-muted-foreground">Email</p>
                <Input
                  type="email"
                  value={form.email}
                  onChange={(e) => setForm((f) => ({ ...f, email: e.target.value }))}
                />
              </div>
              <div className="space-y-1">
                <p className="text-sm text-muted-foreground">Phone</p>
                <Input
                  value={form.phone}
                  onChange={(e) => setForm((f) => ({ ...f, phone: e.target.value }))}
                  placeholder="—"
                />
              </div>
              <div className="space-y-1 sm:col-span-2">
                <p className="text-sm text-muted-foreground">Address</p>
                <textarea
                  value={form.address}
                  onChange={(e) => setForm((f) => ({ ...f, address: e.target.value }))}
                  placeholder="—"
                  rows={3}
                  className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
                />
              </div>
              <DetailField label="Status" value={
                <Badge variant={getStatusColor("member", member.status)} className="capitalize">
                  {member.status}
                </Badge>
              } />
              <DetailField label="Created" value={formatDate(member.created_at)} />
              <DetailField label="Last Updated" value={formatDate(member.updated_at)} />
            </div>
          ) : (
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
              <DetailField label="Name" value={member.name} />
              <DetailField label="Email" value={member.email} />
              <DetailField label="Phone" value={member.phone ?? "—"} />
              <DetailField label="Address" value={member.address ?? "—"} />
              <DetailField label="Status" value={
                <Badge variant={getStatusColor("member", member.status)} className="capitalize">
                  {member.status}
                </Badge>
              } />
              <DetailField label="Created" value={formatDate(member.created_at)} />
              <DetailField label="Last Updated" value={formatDate(member.updated_at)} />
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
          <Button variant="outline" onClick={handleCancelEdit} disabled={saving}>
            Cancel
          </Button>
        </div>
      )}

      {/* Status actions */}
      {!editMode && (
        <div className="flex gap-2">
          {member.status === "active" && (
            <>
              <Button
                variant="destructive"
                onClick={() => handleStatusChange("suspended")}
                disabled={updatingStatus}
              >
                {updatingStatus ? "…" : "Suspend"}
              </Button>
              <Button
                variant="secondary"
                onClick={() => handleStatusChange("inactive")}
                disabled={updatingStatus}
              >
                {updatingStatus ? "…" : "Deactivate"}
              </Button>
            </>
          )}
          {(member.status === "inactive" || member.status === "suspended") && (
            <Button onClick={() => handleStatusChange("active")} disabled={updatingStatus}>
              {updatingStatus ? "…" : "Activate"}
            </Button>
          )}
        </div>
      )}

      {/* Active Borrows */}
      <div className="space-y-3">
        <h2 className="text-lg font-semibold text-stone-800">Active Borrows</h2>
        {activeBorrows.length === 0 ? (
          <p className="text-sm text-stone-400">No active borrows</p>
        ) : (
          <div className="rounded-md border border-stone-200 bg-white">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Book</TableHead>
                  <TableHead>Borrowed</TableHead>
                  <TableHead>Due Date</TableHead>
                  <TableHead>Status</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {activeBorrows.map((borrow) => {
                  const borrowStatus = getBorrowStatus(borrow);
                  return (
                    <TableRow key={borrow.id}>
                      <TableCell>
                        <Link
                          href={`/books/${borrow.book_id}`}
                          className="text-blue-600 hover:underline"
                        >
                          {borrow.book.title}
                        </Link>
                      </TableCell>
                      <TableCell className="text-stone-500">{formatDate(borrow.borrowed_at)}</TableCell>
                      <TableCell className="text-stone-500">{formatDate(borrow.due_date)}</TableCell>
                      <TableCell>
                        <Badge variant={getStatusColor("borrow", borrowStatus)} className="capitalize">
                          {borrowStatus}
                        </Badge>
                      </TableCell>
                    </TableRow>
                  );
                })}
              </TableBody>
            </Table>
          </div>
        )}
      </div>

      {/* Borrow History */}
      <div className="space-y-3">
        <h2 className="text-lg font-semibold text-stone-800">Borrow History</h2>
        {allBorrows.length === 0 ? (
          <p className="text-sm text-stone-400">No borrow history</p>
        ) : (
          <div className="rounded-md border border-stone-200 bg-white">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Book</TableHead>
                  <TableHead>Borrowed</TableHead>
                  <TableHead>Due</TableHead>
                  <TableHead>Returned / Status</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {allBorrows.map((borrow) => {
                  const borrowStatus = getBorrowStatus(borrow);
                  return (
                    <TableRow key={borrow.id}>
                      <TableCell>
                        <Link
                          href={`/books/${borrow.book_id}`}
                          className="text-blue-600 hover:underline"
                        >
                          {borrow.book.title}
                        </Link>
                      </TableCell>
                      <TableCell className="text-stone-500">{formatDate(borrow.borrowed_at)}</TableCell>
                      <TableCell className="text-stone-500">{formatDate(borrow.due_date)}</TableCell>
                      <TableCell>
                        {borrow.returned_at ? (
                          <span className="text-stone-500">{formatDate(borrow.returned_at)}</span>
                        ) : (
                          <Badge variant={getStatusColor("borrow", borrowStatus)} className="capitalize">
                            {borrowStatus}
                          </Badge>
                        )}
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
