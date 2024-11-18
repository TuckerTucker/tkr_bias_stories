// lib/hooks/use-stories.ts
import { useQuery } from "@tanstack/react-query";
import { storiesApi } from "../api/stories";
import type {
  StoryListResponse,
  SingleStoryResponse,
  StoryResponse,
} from "../api/types";

// Simplified query keys
export const storyKeys = {
  all: ["stories"] as const,
  detail: (id: string) => [...storyKeys.all, id] as const,
};

/**
 * Hook to fetch all stories
 */
export function useStories() {
  return useQuery<StoryListResponse, Error>({
    queryKey: storyKeys.all,
    queryFn: storiesApi.getStories,
    select: (data) => ({
      stories: data.stories.map((story) => ({
        ...story,
        responses: Object.entries(story.responses).reduce(
          (acc, [provider, responses]) => {
            const validResponses = responses.filter(storiesApi.isValidResponse);
            if (validResponses.length > 0) {
              acc[provider] = validResponses;
            }
            return acc;
          },
          {} as Record<string, StoryResponse[]>,
        ),
      })),
    }),
  });
}

/**
 * Hook to fetch a single story by ID
 */
export function useStory(id: string) {
  return useQuery<SingleStoryResponse, Error>({
    queryKey: storyKeys.detail(id),
    queryFn: () => storiesApi.getStory(id),
    select: (data) => ({
      story: {
        ...data.story,
        responses: Object.entries(data.story.responses).reduce<
          Record<string, StoryResponse[]>
        >((acc, [provider, responses]) => {
          const validResponses = responses.filter(storiesApi.isValidResponse);
          if (validResponses.length > 0) {
            acc[provider] = validResponses;
          }
          return acc;
        }, {}),
      },
    }),
    enabled: !!id,
  });
}
