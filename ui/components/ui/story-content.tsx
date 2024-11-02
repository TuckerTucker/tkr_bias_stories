// ui/components/ui/story-content.tsx
import { Tabs, TabsList, TabsTrigger, TabsContent } from "./tabs";
import type { Story, ResponseMetadata } from "@/lib/api/types";
import { formatDate } from "@/lib/utils";

interface StoryContentProps {
  story: Story;
}

interface ResponseMetadataProps {
  metadata: ResponseMetadata;
}

const ResponseMetadata = ({ metadata }: ResponseMetadataProps) => (
  <div className="mt-4 space-y-2">
    <h3 className="text-lg font-semibold">Model Details</h3>
    <dl className="grid grid-cols-2 gap-2">
      <dt className="text-muted-foreground">Provider</dt>
      <dd className="capitalize">{metadata.provider}</dd>
      <dt className="text-muted-foreground">Model</dt>
      <dd>{metadata.model}</dd>
      <dt className="text-muted-foreground">Tokens</dt>
      <dd>{metadata.total_tokens}</dd>
      <dt className="text-muted-foreground">Generated</dt>
      <dd>{formatDate(metadata.generated_at)}</dd>
    </dl>
  </div>
);

export function StoryContent({ story }: StoryContentProps) {
  const hasResponses = story.responses &&
    Object.keys(story.responses).length > 0 &&
    Object.values(story.responses).some(arr => arr.length > 0);

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

  const providers = Object.keys(story.responses).filter(
    provider => story.responses[provider].length > 0
  );

  return (
    <div className="w-full max-w-4xl">
      <h1 className="text-2xl font-bold mb-4">{story.title}</h1>
      <p className="text-muted-foreground mb-6">{story.plot}</p>

      <Tabs defaultValue={providers[0]} className="w-full">
        <TabsList className="mb-4">
          {providers.map((provider) => (
            <TabsTrigger key={provider} value={provider} className="capitalize">
              {provider}
            </TabsTrigger>
          ))}
        </TabsList>

        {providers.map((provider) => (
          <TabsContent key={provider} value={provider}>
            <div className="space-y-8">
              {story.responses[provider].map((response, index) => {
                // Parse the text content which might be JSON string
                let displayText = response.text;
                try {
                  const parsed = JSON.parse(response.text);
                  if (parsed.text) {
                    displayText = parsed.text;
                  }
                } catch (e) {
                  // If parsing fails, use the original text
                  console.debug('Response text is not JSON:', e);
                }

                return (
                  <div
                    key={`${response.hero}-${index}`}
                    className="prose dark:prose-invert max-w-none"
                  >
                    <h2 className="text-xl font-semibold mb-4">
                      {response.hero}
                    </h2>
                    <div className="bg-muted p-6 rounded-lg">
                      {displayText ? (
                        <p className="whitespace-pre-wrap">{displayText}</p>
                      ) : (
                        <p>No response text available.</p>
                      )}
                    </div>
                    <ResponseMetadata metadata={response.metadata} />
                  </div>
                );
              })}
            </div>
          </TabsContent>
        ))}
      </Tabs>
    </div>
  );
}
