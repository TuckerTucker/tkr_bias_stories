// ui/lib/api/types.ts
export interface Story {
  id: string;
  title: string;
  plot: string;
  hero: string[];
  path?: string;
}

// Changed StoryResponse to StoryListResponse to match usage
export interface StoryListResponse {
  stories: Story[];
}

// Added separate StoryResponse for single story
export interface StoryResponse {
  story: Story;
}

export interface Version {
  id: string;
  name: string;
  date: string;
}

// Export ApiError interface
export interface ApiError {
  status: number;
  message: string;
}

// lib/api/types.ts

// Define the token usage structure
interface TokenUsage {
  total_tokens: number;
  prompt_tokens?: number;
  completion_tokens?: number;
}

// Define the metadata structure
interface ResponseMetadata {
  model: string;
  usage: TokenUsage;
}

// Define the structure for a single AI response
interface AIResponse {
  text: string;
  metadata: ResponseMetadata;
}

// Define the responses object structure
interface Responses {
  [provider: string]: AIResponse;
}

// Update the Story interface to include responses
export interface Story {
  id: string;
  title: string;
  plot: string;
  hero: string[];
  responses: Responses;
}
