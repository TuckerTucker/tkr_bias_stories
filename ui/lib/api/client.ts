// ui/lib/api/client.ts
import { API_BASE_URL } from "../config/constants";

/**
 * Custom API error class that extends Error
 */
export class ApiError extends Error {
  status: number;

  constructor(status: number, message: string) {
    super(message);
    this.name = "ApiError";
    this.status = status;

    // Required for extending Error in TypeScript
    Object.setPrototypeOf(this, ApiError.prototype);
  }
}

/**
 * Generic fetch wrapper for API calls
 * T represents the expected response type
 */
export async function fetchApi<T>(
  endpoint: string,
  options: RequestInit = {},
): Promise<T> {
  try {
    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
      ...options,
      headers: {
        "Content-Type": "application/json",
        ...options.headers,
      },
    });

    const data = await response.json();

    if (!response.ok) {
      throw new ApiError(
        response.status,
        data.detail || `API error: ${response.statusText}`,
      );
    }

    return data as T;
  } catch (error) {
    // Handle fetch errors and rethrow as ApiError
    if (error instanceof ApiError) {
      throw error;
    }

    // Handle network errors or other fetch failures
    if (error instanceof Error) {
      throw new ApiError(500, `Failed to fetch: ${error.message}`);
    }

    // Handle unknown errors
    throw new ApiError(500, "An unexpected error occurred");
  }
}
