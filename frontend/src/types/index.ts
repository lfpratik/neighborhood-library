export interface Book {
  id: string;
  title: string;
  author: string;
  isbn: string | null;
  publisher: string | null;
  publication_year: number | null;
  genre: string | null;
  status: "available" | "borrowed" | "retired";
  created_at: string;
  updated_at: string;
}

export interface Member {
  id: string;
  name: string;
  email: string;
  phone: string | null;
  address: string | null;
  status: "active" | "inactive" | "suspended";
  created_at: string;
  updated_at: string;
}

export interface Borrow {
  id: string;
  book_id: string;
  member_id: string;
  borrowed_at: string;
  due_date: string;
  returned_at: string | null;
  notes: string | null;
  created_at: string;
  book: Book;
  member: Member;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  size: number;
  pages: number;
}
