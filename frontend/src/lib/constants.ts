export const PAGE_SIZE = 10;

export const API_ENDPOINTS = {
  books: {
    list: "/books",
    detail: (id: string) => `/books/${id}`,
    status: (id: string) => `/books/${id}/status`,
  },
  members: {
    list: "/members",
    detail: (id: string) => `/members/${id}`,
    status: (id: string) => `/members/${id}/status`,
  },
  borrows: {
    list: "/borrows",
    detail: (id: string) => `/borrows/${id}`,
    return: (id: string) => `/borrows/${id}/return`,
  },
} as const;
