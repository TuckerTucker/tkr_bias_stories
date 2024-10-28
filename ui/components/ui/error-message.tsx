// ui/components/ui/error-message.tsx
export function ErrorMessage({
  message = "An error occurred",
}: {
  message?: string;
}) {
  return (
    <div
      data-testid="error-message"
      className="p-4 text-destructive bg-destructive/10 rounded-md"
    >
      <p>{message}</p>
    </div>
  );
}
