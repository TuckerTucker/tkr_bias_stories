// lib/hooks/use-stories.ts
"use client";

import { useQuery } from "@tanstack/react-query";
import { storiesApi } from "../api/stories";

export const storyKeys = {
  all: ["stories"] as const,
  detail: (id: string) => [...storyKeys.all, id] as const,
};

export function useStories() {
  return useQuery({
    queryKey: storyKeys.all,
    queryFn: storiesApi.getStories,
  });
}

export function useStory(id: string) {
  return useQuery({
    queryKey: storyKeys.detail(id),
    queryFn: () => storiesApi.getStory(id),
    enabled: !!id, // Only run query if we have an ID
  });
}
