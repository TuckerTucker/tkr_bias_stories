// ui/components/story-content.tsx
import { Tabs, TabsList, TabsTrigger, TabsContent } from "./tabs";
import type { Story } from "@/lib/api/types";

interface StoryContentProps {
  story: Story;
}

export function StoryContent({ story }: StoryContentProps) {
  return (
    <div className="w-full max-w-4xl">
      <h1 className="text-2xl font-bold mb-4">{story.title}</h1>

      <Tabs defaultValue="anthropic" className="w-full">
        <TabsList className="mb-4">
          <TabsTrigger value="anthropic">Anthropic</TabsTrigger>
          <TabsTrigger value="openai">OpenAI</TabsTrigger>
          <TabsTrigger value="google">Google</TabsTrigger>
        </TabsList>

        {Object.entries(story.responses).map(([provider, response]) => (
          <TabsContent key={provider} value={provider.toLowerCase()}>
            <div className="prose dark:prose-invert max-w-none">
              <div className="bg-muted p-6 rounded-lg">
                <p className="whitespace-pre-wrap">{response.text}</p>
              </div>

              <div className="mt-4">
                <h3 className="text-lg font-semibold">Model Details</h3>
                <dl className="grid grid-cols-2 gap-2 mt-2">
                  <dt className="text-muted-foreground">Model</dt>
                  <dd>{response.metadata.model}</dd>
                  <dt className="text-muted-foreground">Tokens</dt>
                  <dd>{response.metadata.usage.total_tokens}</dd>
                </dl>
              </div>
            </div>
          </TabsContent>
        ))}
      </Tabs>
    </div>
  );
}
