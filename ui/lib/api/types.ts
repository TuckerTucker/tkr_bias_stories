// lib/api/types.ts
// Base Error class that extends built-in Error
export class ApiError extends Error {
  constructor(
    public status: number,
    message: string,
  ) {
    super(message);
    this.name = "ApiError";
    Object.setPrototypeOf(this, ApiError.prototype);
  }
}

// Base metadata structure
export interface ResponseMetadata {
  provider: "anthropic" | "openai";
  model: string;
  total_tokens: number;
  generated_at: string;
}

// Base response structure matching backend StoryResponse
export interface StoryResponse {
  story_id: string;
  hero: string;
  text: string;
  metadata: ResponseMetadata;
  generated_at: string;
}

// Core story structure without status tracking
export interface StoryOutline {
  id: string;
  title: string;
  plot: string;
  hero: string[]; // Array order is source of truth
}

// Extended story interface with responses
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
