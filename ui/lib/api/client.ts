// lib/api/client.ts
import { API_BASE_URL } from "../config/constants";
import type { ApiError as IApiError } from "./types";

class ApiError extends Error implements IApiError {
  status: number;

  constructor(status: number, message: string) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

export async function fetchApi<T>(
  endpoint: string,
  options: RequestInit = {},
): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${endpoint}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...options.headers,
    },
  });

  const data = await response.json();

  if (!response.ok) {
    throw new ApiError(response.status, data.detail || "An error occurred");
  }

  return data as T;
}

export { ApiError };
