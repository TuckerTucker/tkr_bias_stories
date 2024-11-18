// lib/api/stories.ts
import { fetchApi } from "./client";
import { API_ROUTES } from "../config/constants";
import type {
  StoryListResponse,
  SingleStoryResponse,
  StoryResponse,
  ResponseMetadata,
} from "./types";

export const storiesApi = {
  /**
   * Get all stories with their responses
   */
  getStories: async (): Promise<StoryListResponse> => {
    return fetchApi<StoryListResponse>(API_ROUTES.stories);
  },

  /**
   * Get a single story by ID
   */
  getStory: async (id: string): Promise<SingleStoryResponse> => {
    return fetchApi<SingleStoryResponse>(API_ROUTES.story(id));
  },

  /**
   * Validate metadata structure
   */
  isValidMetadata: (metadata: unknown): metadata is ResponseMetadata => {
    if (!metadata || typeof metadata !== "object") {
      return false;
    }

    const m = metadata as Partial<ResponseMetadata>;
    return (
      typeof m.provider === "string" &&
      typeof m.model === "string" &&
      typeof m.total_tokens === "number" &&
      typeof m.generated_at === "string"
    );
  },

  /**
   * Validate story response format
   */
  isValidResponse: (response: unknown): response is StoryResponse => {
    if (!response || typeof response !== "object") {
      return false;
    }

    const r = response as Partial<StoryResponse>;
    if (
      typeof r.story_id !== "string" ||
      typeof r.hero !== "string" ||
      typeof r.text !== "string" ||
      !r.metadata
    ) {
      return false;
    }

    return storiesApi.isValidMetadata(r.metadata);
  },

  /**
   * Process response text which might be JSON string
   */
  processResponseText: (text: string): string => {
    try {
      const parsed = JSON.parse(text);
      return parsed.text || text;
    } catch {
      return text;
    }
  },
};

export default storiesApi;
