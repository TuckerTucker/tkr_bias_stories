// components/library-page.tsx
"use client";

import { useState, useCallback } from "react";
import { ScrollArea } from "@/components/ui/scroll-area";
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/components/ui/collapsible";
import { BookIcon, ChevronRightIcon } from "lucide-react";
import { GitHubLogoIcon } from "@radix-ui/react-icons";
import { useStories } from "@/lib/hooks/use-stories";
import { useStorySorting } from "@/lib/hooks/use-story-sorting";
import { useNavigation } from "@/lib/context/navigation-context";
import { LoadingSpinner } from "@/components/ui/loading-spinner";
import { StoryContent } from "@/components/ui/story-content";
import { ErrorMessage } from "@/components/ui/error-message";
import { StorySort } from "@/components/ui/story-sort";
import { HeroItem } from "@/components/ui/hero-item";
import { DarkModeToggleComponent } from "@/components/ui/dark-mode-toggle";
import type { Story } from "@/lib/api/types";

export function LibraryPage() {
  const [expandedItem, setExpandedItem] = useState<string | null>(null);
  const [selectedStory, setSelectedStory] = useState<Story | null>(null);

  // Get navigation context for hero selection
  const { selectHero, clearSelection } = useNavigation();

  // Fetch stories
  const { data, isLoading, error } = useStories();

  // Setup sorting with original order preservation
  const {
    sortConfig,
    sortedStories,
    updateSort,
    toggleDirection,
    resetSort,
    //originalHeroOrder
  } = useStorySorting(data?.stories || []);

  const toggleItem = useCallback(
    (itemId: string) => {
      setExpandedItem((prevExpanded) => {
        const isExpanding = prevExpanded !== itemId;

        if (sortedStories) {
          const story = sortedStories.find((s) => s.id === itemId);

          if (isExpanding && story) {
            // Expanding a story
            setSelectedStory(story);

            // Select first hero if available, using original order
            if (story.hero.length > 0) {
              const firstHero = story.hero[0]; // Will be in original order

              // Find first provider with responses
              const firstProvider =
                Object.keys(story.responses).find(
                  (provider) => story.responses[provider]?.length > 0,
                ) || "anthropic";

              selectHero({
                storyId: story.id,
                provider: firstProvider,
                heroName: firstHero,
              });
            }
          } else {
            // Collapsing current story
            setSelectedStory(null);
            clearSelection();
          }
        }

        return isExpanding ? itemId : null;
      });
    },
    [sortedStories, selectHero, clearSelection],
  );

  if (isLoading) return <LoadingSpinner />;
  if (error) return <ErrorMessage message={error.message} />;
  if (!sortedStories?.length)
    return <ErrorMessage message="No stories found" />;

  return (
    <div className="flex h-screen bg-background">
      {/* Sidebar */}
      <aside className="w-80 border-r flex flex-col">
        {/* Header */}
        <div className="p-4 border-b">
          <h2 className="text-lg font-semibold">Story Library</h2>
          <StorySort
            config={sortConfig}
            onUpdateSort={updateSort}
            onToggleDirection={toggleDirection}
            onReset={resetSort}
            disableDirection={sortConfig.primary === 'originalOrder'}
          />
        </div>

        {/* Story List */}
        <ScrollArea className="flex-grow">
          <nav className="p-4 space-y-2">
            {sortedStories.map((story) => (
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
                      <ul className="space-y-1 mt-1">
                        {/* Use original hero order from story */}
                        {story.hero.map((heroName, index) => (
                          <HeroItem
                            key={`${story.id}-hero-${index}`}
                            storyId={story.id}
                            heroName={heroName}
                            index={index}
                          />
                        ))}
                      </ul>
                    </div>
                  </div>
                </CollapsibleContent>
              </Collapsible>
            ))}
          </nav>
        </ScrollArea>

        {/* Footer Controls */}
        <div className="border-t">
          <div className="flex items-center justify-between px-4">
            <DarkModeToggleComponent />
            <a
              href="https://github.com/tuckertucker/tkr_bias_stories"
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center justify-center p-4 text-muted-foreground hover:text-foreground transition-colors"
              aria-label="View GitHub Repository"
            >
              <GitHubLogoIcon className="h-5 w-5" />
            </a>
          </div>
        </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 p-6 overflow-auto scroll-smooth">
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
