// components/ui/error-state.tsx
import { AlertTriangle } from "lucide-react";
import { Button } from "./button";

interface ErrorStateProps {
  title?: string;
  message: string;
  onDismiss?: () => void;
}

export function ErrorState({
  title = "Error",
  message,
  onDismiss,
}: ErrorStateProps) {
  return (
    <div
      className="rounded-lg border border-destructive/50 p-6 space-y-4"
      data-testid="error-state"
    >
      <div className="flex items-start space-x-4">
        <div className="rounded-full bg-destructive/10 p-2">
          <AlertTriangle className="h-6 w-6 text-destructive" />
        </div>
        <div className="flex-1 space-y-2">
          <h3 className="font-semibold text-destructive">{title}</h3>
          <p className="text-sm text-muted-foreground">{message}</p>
        </div>
      </div>

      {onDismiss && (
        <div className="flex justify-end">
          <Button
            variant="ghost"
            onClick={onDismiss}
            data-testid="error-dismiss"
          >
            Dismiss
          </Button>
        </div>
      )}
    </div>
  );
}
