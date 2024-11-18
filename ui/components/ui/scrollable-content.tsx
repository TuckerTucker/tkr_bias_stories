// components/ui/scrollable-content.tsx
import { Story, StoryResponse } from "@/lib/api/types";
import { generateHeroId } from "@/lib/utils/navigation";
import { ScrollPositionTracker } from "@/components/ui/scroll-position-tracker";
import { storiesApi } from "@/lib/api/stories";

interface ScrollableContentProps {
  story: Story;
  selectedHero: { heroName: string } | null;
  activeProvider: string | null;
  responses: StoryResponse[];
}

export function ScrollableContent({
  story,
  selectedHero,
  activeProvider,
  responses
}: ScrollableContentProps) {
  if (!activeProvider) return null;

  return (
    <div className="flex-1 overflow-y-auto pt-4">
      {selectedHero ? (
        // Single hero view
        responses.map(response => {
          if (response.hero !== selectedHero.heroName) return null;

          return (
            <div
              key={`${activeProvider}-${response.hero}`}
              id={generateHeroId(story.id, activeProvider, response.hero)}
              className="prose dark:prose-invert max-w-none scroll-m-20"
            >
              <ScrollPositionTracker
                storyId={story.id}
                heroName={response.hero}
              />
              <h2 className="text-xl font-semibold mb-1">{response.hero}</h2>
              <p className="text-sm text-muted-foreground mb-4">
                {response.metadata.model}
              </p>
              <div className="bg-muted p-6 rounded-lg">
                <p className="whitespace-pre-wrap">
                  {storiesApi.processResponseText(response.text)}
                </p>
              </div>
            </div>
          );
        })
      ) : (
        // All heroes view
        responses.map(response => (
          <div
            key={`${activeProvider}-${response.hero}`}
            id={generateHeroId(story.id, activeProvider, response.hero)}
            className="prose dark:prose-invert max-w-none scroll-m-20 mb-8 last:mb-0"
          >
            <ScrollPositionTracker
              storyId={story.id}
              heroName={response.hero}
            />
            <h2 className="text-xl font-semibold mb-1">{response.hero}</h2>
            <p className="text-sm text-muted-foreground mb-4">
              {response.metadata.model}
            </p>
            <div className="bg-muted p-6 rounded-lg">
              <p className="whitespace-pre-wrap">
                {storiesApi.processResponseText(response.text)}
              </p>
            </div>
          </div>
        ))
      )}
    </div>
  );
}
