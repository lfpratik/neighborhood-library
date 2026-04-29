import type { Book, Member, Borrow, PaginatedResponse } from "@/types";

const API_URL =
  process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

async function fetchAPI<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_URL}${path}`, {
    headers: { "Content-Type": "application/json", ...options?.headers },
    ...options,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err?.detail?.message || `API error: ${res.status}`);
  }
  return res.json();
}

function buildQuery(
  params?: Record<string, string | number | boolean | null | undefined>,
): string {
  if (!params) return "";
  const entries = Object.entries(params).filter(
    ([, v]) => v != null && v !== "",
  );
  if (!entries.length) return "";
  return (
    "?" +
    new URLSearchParams(entries.map(([k, v]) => [k, String(v)])).toString()
  );
}

export function getBook(id: string): Promise<Book> {
  return fetchAPI(`/books/${id}`);
}

export function updateBook(id: string, data: Partial<Book>): Promise<Book> {
  return fetchAPI(`/books/${id}`, {
    method: "PATCH",
    body: JSON.stringify(data),
  });
}

export function getBooks(
  params?: Partial<{
    status: string;
    search: string;
    page: number;
    size: number;
  }>,
): Promise<PaginatedResponse<Book>> {
  return fetchAPI(`/books${buildQuery(params)}`);
}

export function createBook(data: Partial<Book>): Promise<Book> {
  return fetchAPI("/books", { method: "POST", body: JSON.stringify(data) });
}

export function updateBookStatus(
  id: string,
  status: Book["status"],
): Promise<Book> {
  return fetchAPI(`/books/${id}/status`, {
    method: "PATCH",
    body: JSON.stringify({ status }),
  });
}

export function getMember(id: string): Promise<Member> {
  return fetchAPI(`/members/${id}`);
}

export function updateMember(
  id: string,
  data: Partial<Member>,
): Promise<Member> {
  return fetchAPI(`/members/${id}`, {
    method: "PATCH",
    body: JSON.stringify(data),
  });
}

export function getMembers(
  params?: Partial<{
    status: string;
    search: string;
    page: number;
    size: number;
  }>,
): Promise<PaginatedResponse<Member>> {
  return fetchAPI(`/members${buildQuery(params)}`);
}

export function createMember(data: Partial<Member>): Promise<Member> {
  return fetchAPI("/members", { method: "POST", body: JSON.stringify(data) });
}

export function updateMemberStatus(
  id: string,
  status: Member["status"],
): Promise<Member> {
  return fetchAPI(`/members/${id}/status`, {
    method: "PATCH",
    body: JSON.stringify({ status }),
  });
}

export function getBorrow(id: string): Promise<Borrow> {
  return fetchAPI(`/borrows/${id}`);
}

export function getBorrows(
  params?: Partial<{
    member_id: string;
    book_id: string;
    active: boolean;
    overdue: boolean;
    page: number;
    size: number;
  }>,
): Promise<PaginatedResponse<Borrow>> {
  return fetchAPI(`/borrows${buildQuery(params)}`);
}

export function createBorrow(data: {
  book_id: string;
  member_id: string;
  notes?: string;
}): Promise<Borrow> {
  return fetchAPI("/borrows", { method: "POST", body: JSON.stringify(data) });
}

export function returnBorrow(id: string): Promise<Borrow> {
  return fetchAPI(`/borrows/${id}/return`, { method: "PATCH" });
}
