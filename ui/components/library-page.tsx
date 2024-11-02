// ui/components/library-page.tsx
"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/components/ui/collapsible";
import { PlusIcon, BookIcon, ChevronRightIcon } from "lucide-react";
import { useStories } from "@/lib/hooks/use-stories";
import { ErrorMessage } from "@/components/ui/error-message";
import { LoadingSpinner } from "@/components/ui/loading-spinner";
import { StoryContent } from "@/components/ui/story-content";
import type { Story } from "@/lib/api/types";

export function LibraryPage() {
  const [expandedItem, setExpandedItem] = useState<string | null>(null);
  const [selectedStory, setSelectedStory] = useState<Story | null>(null);
  const { data, isLoading, error } = useStories();

  const toggleItem = (itemId: string) => {
    setExpandedItem(expandedItem === itemId ? null : itemId);
    if (data) {
      const story = data.stories.find((s) => s.id === itemId);
      setSelectedStory(story || null);
    }
  };

  if (isLoading) return <LoadingSpinner />;
  if (error) return <ErrorMessage message={error.message} />;
  if (!data?.stories.length) return <ErrorMessage message="No stories found" />;

  return (
    <div className="flex h-screen bg-background">
      <aside className="w-80 border-r flex flex-col">
        <div className="p-4 border-b">
          <h2 className="text-lg font-semibold">Story Library</h2>
        </div>

        <ScrollArea className="flex-grow">
          <nav className="p-4 space-y-2">
            {data.stories.map((story) => (
              <Collapsible
                key={story.id}
                open={expandedItem === story.id}
                onOpenChange={() => toggleItem(story.id)}
              >
                <CollapsibleTrigger
                  className="flex items-center justify-between w-full text-sm hover:bg-accent hover:text-accent-foreground rounded-md p-2 transition-colors"
                  data-testid={`story-trigger-${story.id}`}
                >
                  <div className="flex items-center space-x-2">
                    <BookIcon className="h-4 w-4" />
                    <span className="flex-1 truncate">{story.title}</span>
                  </div>
                  <ChevronRightIcon
                    className={`h-4 w-4 transition-transform duration-200 ${
                      expandedItem === story.id ? "transform rotate-90" : ""
                    }`}
                  />
                </CollapsibleTrigger>

                <CollapsibleContent
                  className="pl-6 pr-2 py-2"
                  data-testid={`story-content-${story.id}`}
                >
                  <div className="text-sm text-muted-foreground">
                    <p>{story.plot}</p>
                    <div className="mt-2">
                      <h4 className="font-medium">Heroes:</h4>
                      <ul className="list-disc list-inside">
                        {story.hero.map((hero, index) => (
                          <li
                            key={`${story.id}-hero-${index}`}
                            className="truncate"
                            data-testid={`hero-${story.id}-${index}`}
                          >
                            {hero}
                          </li>
                        ))}
                      </ul>
                    </div>
                  </div>
                </CollapsibleContent>
              </Collapsible>
            ))}
          </nav>
        </ScrollArea>

        <div className="p-4 border-t">
          <Button
            className="w-full"
            variant="outline"
            data-testid="new-template-button"
          >
            <PlusIcon className="h-4 w-4 mr-2" />
            New Story Template
          </Button>
        </div>
      </aside>

      <main className="flex-1 p-6 overflow-auto">
        {selectedStory ? (
          <StoryContent story={selectedStory} />
        ) : (
          <div className="flex flex-col items-center justify-center h-full text-center space-y-4">
            <h1 className="text-2xl font-bold">
              Exposing The Bias In AI With Storytelling
            </h1>
            <p className="max-w-md text-muted-foreground">
              AI models were trained on data from the internet.
              <br />
              The Internet is full of bias.
              <br />
              So, how do we expose the biases trained into the AI?
              <br />
              Ask it to tell us a story.
            </p>
          </div>
        )}
      </main>
    </div>
  );
}
