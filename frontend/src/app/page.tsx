"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { BookOpen, Users, ArrowLeftRight, AlertTriangle, CheckCircle2 } from "lucide-react";
import { getBooks, getMembers, getBorrows } from "@/lib/api";
import { formatDate, isOverdue } from "@/lib/utils";
import type { Borrow } from "@/types";

interface DashboardData {
  totalBooks: number;
  activeMembers: number;
  activeBorrows: number;
  overdueBorrows: number;
  recentBorrows: Borrow[];
}

function SkeletonCard() {
  return (
    <Card>
      <CardHeader className="pb-2">
        <div className="h-4 w-24 bg-stone-200 rounded animate-pulse" />
      </CardHeader>
      <CardContent>
        <div className="h-9 w-16 bg-stone-200 rounded animate-pulse" />
      </CardContent>
    </Card>
  );
}

export default function DashboardPage() {
  const [loading, setLoading] = useState(true);
  const [data, setData] = useState<DashboardData | null>(null);

  useEffect(() => {
    Promise.all([
      getBooks({ size: 1 }),
      getMembers({ status: "active", size: 1 }),
      getBorrows({ active: true, size: 1 }),
      getBorrows({ overdue: true, size: 1 }),
      getBorrows({ size: 5 }),
    ]).then(([books, members, activeBorrows, overdueBorrows, recentBorrows]) => {
      setData({
        totalBooks: books.total,
        activeMembers: members.total,
        activeBorrows: activeBorrows.total,
        overdueBorrows: overdueBorrows.total,
        recentBorrows: recentBorrows.items,
      });
    }).finally(() => setLoading(false));
  }, []);

  const statCards = [
    { label: "Total Books", icon: BookOpen, value: data?.totalBooks },
    { label: "Active Members", icon: Users, value: data?.activeMembers },
    { label: "Active Borrows", icon: ArrowLeftRight, value: data?.activeBorrows },
  ];

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-semibold text-stone-800">Dashboard</h1>

      {/* Stat Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {loading
          ? [0, 1, 2].map((i) => <SkeletonCard key={i} />)
          : statCards.map(({ label, icon: Icon, value }) => (
              <Card key={label}>
                <CardHeader className="flex flex-row items-center justify-between pb-2">
                  <CardTitle className="text-sm font-medium text-stone-500">{label}</CardTitle>
                  <Icon className="w-4 h-4 text-stone-400" />
                </CardHeader>
                <CardContent>
                  <p className="text-3xl font-bold text-stone-800">{value ?? "—"}</p>
                </CardContent>
              </Card>
            ))}
      </div>

      {/* Overdue Alert */}
      {!loading && data && (
        data.overdueBorrows > 0 ? (
          <div className="flex items-center gap-3 rounded-lg border border-amber-200 bg-amber-50 px-4 py-3 text-amber-800">
            <AlertTriangle className="w-5 h-5 shrink-0 text-amber-600" />
            <span className="text-sm font-medium">
              {data.overdueBorrows} overdue {data.overdueBorrows === 1 ? "borrow" : "borrows"} —{" "}
            </span>
            <Link href="/borrows" className="text-sm font-semibold underline underline-offset-2 hover:text-amber-900">
              View borrows
            </Link>
          </div>
        ) : (
          <div className="flex items-center gap-3 rounded-lg border border-green-200 bg-green-50 px-4 py-3 text-green-800">
            <CheckCircle2 className="w-5 h-5 shrink-0 text-green-600" />
            <span className="text-sm font-medium">All books returned on time</span>
          </div>
        )
      )}

      {/* Recent Borrows */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base font-semibold text-stone-800">Recent Borrows</CardTitle>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="space-y-3">
              {[0, 1, 2].map((i) => (
                <div key={i} className="h-5 bg-stone-200 rounded animate-pulse" />
              ))}
            </div>
          ) : data?.recentBorrows.length === 0 ? (
            <p className="text-sm text-stone-400">No borrows yet.</p>
          ) : (
            <ul className="divide-y divide-stone-100">
              {data?.recentBorrows.map((borrow) => {
                const overdue = isOverdue(borrow.due_date, borrow.returned_at);
                const borrowStatus = borrow.returned_at ? "returned" : overdue ? "overdue" : "active";
                const badgeVariant =
                  borrowStatus === "returned" ? "default" :
                  borrowStatus === "overdue" ? "destructive" : "secondary";
                return (
                  <li key={borrow.id} className="flex items-center justify-between py-2.5">
                    <span className="text-sm text-stone-700">
                      <span className="font-medium">{borrow.member.name}</span>
                      {" borrowed "}
                      <span className="font-medium">{borrow.book.title}</span>
                      {" — due "}
                      <span className="text-stone-500">{formatDate(borrow.due_date)}</span>
                    </span>
                    <Badge variant={badgeVariant} className="ml-4 capitalize shrink-0">
                      {borrowStatus}
                    </Badge>
                  </li>
                );
              })}
            </ul>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
