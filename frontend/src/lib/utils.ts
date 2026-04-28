import { clsx, type ClassValue } from "clsx"
import { twMerge } from "tailwind-merge"

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

export function formatDate(isoString: string): string {
  return new Date(isoString).toLocaleDateString("en-US", {
    year: "numeric",
    month: "short",
    day: "numeric",
  });
}

export function formatDateTime(isoString: string): string {
  return new Date(isoString).toLocaleString("en-US", {
    year: "numeric",
    month: "short",
    day: "numeric",
    hour: "numeric",
    minute: "2-digit",
  });
}

export function getStatusColor(
  entity: "book" | "member" | "borrow",
  status: string
): "default" | "secondary" | "destructive" | "outline" {
  if (entity === "book") {
    if (status === "available") return "default";
    if (status === "borrowed") return "secondary";
    return "outline";
  }
  if (entity === "member") {
    if (status === "active") return "default";
    if (status === "suspended") return "destructive";
    return "outline";
  }
  // borrow
  if (status === "active") return "secondary";
  if (status === "overdue") return "destructive";
  return "default";
}

export function isOverdue(due_date: string, returned_at: string | null): boolean {
  if (returned_at !== null) return false;
  return new Date() > new Date(due_date);
}
