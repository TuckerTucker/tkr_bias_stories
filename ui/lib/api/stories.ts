// lib/api/stories.ts

import { fetchApi } from "./client";
import { API_ROUTES } from "../config/constants";
import type { StoryListResponse, StoryResponse } from "./types";

export const storiesApi = {
  // Get all stories
  getStories: async (): Promise<StoryListResponse> => {
    return fetchApi<StoryListResponse>(API_ROUTES.stories);
  },

  // Get a specific story by ID
  getStory: async (id: string): Promise<StoryResponse> => {
    return fetchApi<StoryResponse>(API_ROUTES.story(id));
  },
};
