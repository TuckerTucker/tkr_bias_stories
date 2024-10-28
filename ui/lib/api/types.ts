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
