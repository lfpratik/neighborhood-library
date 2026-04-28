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
import { updateMemberStatus } from "@/lib/api";
import { getStatusColor } from "@/lib/utils";
import type { Member } from "@/types";

interface Props {
  members: Member[];
  onRefresh: () => void;
}

export default function MemberTable({ members, onRefresh }: Props) {
  const [updating, setUpdating] = useState<string | null>(null);

  async function handleStatusChange(member: Member, newStatus: Member["status"]) {
    setUpdating(member.id);
    try {
      await updateMemberStatus(member.id, newStatus);
      toast.success(`${member.name} ${newStatus}`);
      onRefresh();
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Failed to update member");
    } finally {
      setUpdating(null);
    }
  }

  if (members.length === 0) {
    return (
      <div className="rounded-md border border-stone-200 bg-white px-6 py-12 text-center">
        <p className="text-sm text-stone-400">No members found</p>
      </div>
    );
  }

  return (
    <div className="rounded-md border border-stone-200 bg-white">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Name</TableHead>
            <TableHead>Email</TableHead>
            <TableHead>Phone</TableHead>
            <TableHead>Status</TableHead>
            <TableHead className="w-48">Actions</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {members.map((member) => (
            <TableRow key={member.id}>
              <TableCell className="font-medium text-stone-800">{member.name}</TableCell>
              <TableCell className="text-stone-600">{member.email}</TableCell>
              <TableCell className="text-stone-500">{member.phone ?? "—"}</TableCell>
              <TableCell>
                <Badge variant={getStatusColor("member", member.status)} className="capitalize">
                  {member.status}
                </Badge>
              </TableCell>
              <TableCell>
                <div className="flex gap-2">
                  {member.status === "active" && (
                    <>
                      <Button
                        size="sm"
                        variant="destructive"
                        disabled={updating === member.id}
                        onClick={() => handleStatusChange(member, "suspended")}
                      >
                        {updating === member.id ? "…" : "Suspend"}
                      </Button>
                      <Button
                        size="sm"
                        variant="outline"
                        disabled={updating === member.id}
                        onClick={() => handleStatusChange(member, "inactive")}
                      >
                        {updating === member.id ? "…" : "Deactivate"}
                      </Button>
                    </>
                  )}
                  {(member.status === "inactive" || member.status === "suspended") && (
                    <Button
                      size="sm"
                      variant="default"
                      disabled={updating === member.id}
                      onClick={() => handleStatusChange(member, "active")}
                    >
                      {updating === member.id ? "…" : "Activate"}
                    </Button>
                  )}
                </div>
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  );
}
