// lib/config/constants.ts

// Use environment variable if defined, otherwise fallback to localhost
export const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";
export const API_ROUTES = {
  stories: "/api/stories",
  story: (id: string) => `/api/stories/${id}`
} as const;
