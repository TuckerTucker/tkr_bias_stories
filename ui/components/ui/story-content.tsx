// ui/components/ui/story-content.tsx
import { Tabs, TabsList, TabsTrigger, TabsContent } from "./tabs";
import type { Story } from "@/lib/api/types";

interface StoryContentProps {
  story: Story;
}

export function StoryContent({ story }: StoryContentProps) {
  // Early return if no responses
  if (!story.responses) {
    return (
      <div className="w-full max-w-4xl">
        <h1 className="text-2xl font-bold mb-4">{story.title}</h1>
        <div className="bg-muted p-6 rounded-lg">
          <p>No responses available for this story yet.</p>
        </div>
      </div>
    );
  }

  // Check if responses object is empty
  const hasResponses = Object.keys(story.responses).length > 0;
  if (!hasResponses) {
    return (
      <div className="w-full max-w-4xl">
        <h1 className="text-2xl font-bold mb-4">{story.title}</h1>
        <div className="bg-muted p-6 rounded-lg">
          <p>No responses available for this story yet.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="w-full max-w-4xl">
      <h1 className="text-2xl font-bold mb-4">{story.title}</h1>

      <Tabs defaultValue="anthropic" className="w-full">
        <TabsList className="mb-4">
          {Object.keys(story.responses).map((provider) => (
            <TabsTrigger key={provider} value={provider.toLowerCase()}>
              {provider}
            </TabsTrigger>
          ))}
        </TabsList>

        {Object.entries(story.responses).map(([provider, response]) => (
          <TabsContent key={provider} value={provider.toLowerCase()}>
            <div className="prose dark:prose-invert max-w-none">
              <div className="bg-muted p-6 rounded-lg">
                {response?.text ? (
                  <p className="whitespace-pre-wrap">{response.text}</p>
                ) : (
                  <p>No response text available.</p>
                )}
              </div>

              {response?.metadata && (
                <div className="mt-4">
                  <h3 className="text-lg font-semibold">Model Details</h3>
                  <dl className="grid grid-cols-2 gap-2 mt-2">
                    <dt className="text-muted-foreground">Model</dt>
                    <dd>{response.metadata.model}</dd>
                    <dt className="text-muted-foreground">Tokens</dt>
                    <dd>{response.metadata.usage?.total_tokens}</dd>
                  </dl>
                </div>
              )}
            </div>
          </TabsContent>
        ))}
      </Tabs>
    </div>
  );
}
