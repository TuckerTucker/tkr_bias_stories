// components/ui/story-header.tsx
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import type { Story } from "@/lib/api/types";

interface StoryHeaderProps {
  story: Story;
  activeProvider: string | null;
  onProviderChange: (provider: string) => void;
  providers: string[];
}

export function StoryHeader({
  story,
  activeProvider,
  onProviderChange,
  providers
}: StoryHeaderProps) {
  return (
    <div className="sticky top-0 z-10 bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60 border-b pb-4">
      <div className="space-y-4">
        <h1 className="text-2xl font-bold">{story.title}</h1>

        <div className="flex items-center justify-between">
          <Tabs
            defaultValue={activeProvider || providers[0]}
            value={activeProvider || providers[0]}
            onValueChange={onProviderChange}
            className="w-full max-w-[400px]"
          >
            <TabsList>
              {providers.map((provider) => (
                <TabsTrigger
                  key={provider}
                  value={provider}
                  className="capitalize"
                >
                  {provider}
                </TabsTrigger>
              ))}
            </TabsList>
          </Tabs>
        </div>
      </div>
    </div>
  );
}
