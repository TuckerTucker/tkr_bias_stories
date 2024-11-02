// ui/lib/api/stories.ts
import { fetchApi } from "./client";
import { API_ROUTES } from "../config/constants";
import {
  StoryListResponse,
  SingleStoryResponse,
  StoryResponse,
  ResponseMetadata
} from "./types";

export const storiesApi = {
  getStories: async (): Promise<StoryListResponse> => {
    return fetchApi<StoryListResponse>(API_ROUTES.stories);
  },

  getStory: async (id: string): Promise<SingleStoryResponse> => {
    return fetchApi<SingleStoryResponse>(API_ROUTES.story(id));
  },

  isValidResponse: (response: unknown): response is StoryResponse => {
    if (!response || typeof response !== 'object') {
      console.debug('Response is not an object');
      return false;
    }

    const r = response as Partial<StoryResponse>;

    // Check required fields
    const hasRequiredFields = (
      typeof r.story_id === 'string' &&
      typeof r.hero === 'string' &&
      typeof r.text === 'string' &&
      r.metadata !== undefined &&
      typeof r.metadata === 'object'
    );

    if (!hasRequiredFields) {
      console.debug('Missing required fields');
      return false;
    }

    // Check metadata structure
    const metadata = r.metadata as Partial<ResponseMetadata>;
    const hasValidMetadata = (
      typeof metadata.provider === 'string' &&
      typeof metadata.model === 'string' &&
      typeof metadata.total_tokens === 'number' &&
      typeof metadata.generated_at === 'string'
    );

    if (!hasValidMetadata) {
      console.debug('Invalid metadata structure');
    }

    return hasValidMetadata;
  }
};
