"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { BookOpen, Users, ArrowLeftRight, LayoutDashboard, Library } from "lucide-react";
import { cn } from "@/lib/utils";

const navItems = [
  { href: "/", label: "Dashboard", icon: LayoutDashboard },
  { href: "/books", label: "Books", icon: BookOpen },
  { href: "/members", label: "Members", icon: Users },
  { href: "/borrows", label: "Borrows", icon: ArrowLeftRight },
];

export default function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="fixed left-0 top-0 h-full w-64 bg-stone-50 border-r border-stone-200 flex flex-col">
      <div className="flex items-center gap-2 px-6 py-5 border-b border-stone-200">
        <Library className="w-6 h-6 text-amber-700" />
        <span className="font-semibold text-stone-800 text-sm leading-tight">
          Neighborhood Library
        </span>
      </div>
      <nav className="flex-1 px-3 py-4 space-y-1">
        {navItems.map(({ href, label, icon: Icon }) => {
          const isActive = href === "/" ? pathname === "/" : pathname.startsWith(href);
          return (
            <Link
              key={href}
              href={href}
              className={cn(
                "flex items-center gap-3 px-3 py-2 rounded-md text-sm font-medium transition-colors",
                isActive
                  ? "bg-stone-200 text-stone-900"
                  : "text-stone-600 hover:bg-stone-100 hover:text-stone-900"
              )}
            >
              <Icon className="w-4 h-4" />
              {label}
            </Link>
          );
        })}
      </nav>
    </aside>
  );
}
