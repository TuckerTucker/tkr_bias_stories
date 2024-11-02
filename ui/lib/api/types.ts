// ui/lib/api/types.ts

// Base Error type
export interface ApiError {
  status: number;
  message: string;
}

// Base metadata structure
export interface ResponseMetadata {
  provider: 'anthropic' | 'openai';
  model: string;
  total_tokens: number;
  generated_at: string;
}

// Base response structure matching our backend StoryResponse
export interface StoryResponse {
  story_id: string;
  hero: string;
  text: string;
  metadata: ResponseMetadata;
}

// Story outline structure
export interface StoryOutline {
  id: string;
  title: string;
  plot: string;
  hero: string[];
}

// Combined story data with responses
export interface Story extends StoryOutline {
  responses: {
    [provider: string]: StoryResponse[];
  };
}

// API response types
export interface StoryListResponse {
  stories: Story[];
}

export interface SingleStoryResponse {
  story: Story;
}
