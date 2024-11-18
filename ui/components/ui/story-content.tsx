// tkr_bias_stories/ui/components/ui/story-content.tsx

import { useNavigation } from "@/lib/context/navigation-context";
import { StoryHeader } from "@/components/ui/story-header";
import { ScrollableContent } from "@/components/ui/scrollable-content";
import { ErrorState } from "@/components/ui/error-state";
import type { Story } from "@/lib/api/types";
import { useEffect } from "react";

interface StoryContentProps {
  story: Story;
}

export function StoryContent({ story }: StoryContentProps) {
  const { selectedHero, activeProvider, setProvider, selectHero } =
    useNavigation();

  // Get providers with existing responses
  const providers = Object.keys(story.responses).filter(
    (provider) => story.responses[provider]?.length > 0,
  );

  // Get current provider's responses
  const currentResponses = activeProvider
    ? story.responses[activeProvider]
    : [];

  // Effect to handle ONLY initial provider and hero selection
  useEffect(() => {
    // Only run this effect if we have no provider AND no selected hero
    // This ensures it only runs on first load
    if (!activeProvider && !selectedHero && providers.length > 0) {
      const firstProvider = providers[0];
      setProvider(firstProvider);

      // Only select first hero if we don't have any hero selected
      if (story.hero.length > 0) {
        selectHero({
          storyId: story.id,
          provider: firstProvider,
          heroName: story.hero[0],
        });
      }
    }
  }, [story, providers, activeProvider, selectedHero, setProvider, selectHero]);

  // Handle case where story has no responses
  if (!providers.length) {
    return (
      <div className="w-full max-w-4xl mx-auto p-6">
        <h1 className="text-2xl font-bold mb-6">{story.title}</h1>
        <ErrorState
          title="No Responses Available"
          message="This story doesn't have any AI-generated responses yet."
        />
      </div>
    );
  }

  // Handle case where story has no heroes
  if (!story.hero.length) {
    return (
      <div className="w-full max-w-4xl mx-auto p-6">
        <h1 className="text-2xl font-bold mb-6">{story.title}</h1>
        <ErrorState
          title="No Heroes Defined"
          message="This story doesn't have any heroes defined."
        />
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full max-w-4xl mx-auto">
      <StoryHeader
        story={story}
        activeProvider={activeProvider}
        onProviderChange={(provider) => {
          setProvider(provider);
          // We no longer need to handle hero selection here as it's maintained in the context
        }}
        providers={providers}
      />

      <ScrollableContent
        story={story}
        selectedHero={selectedHero}
        activeProvider={activeProvider}
        responses={currentResponses}
      />
    </div>
  );
}
