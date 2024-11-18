import { AlertTriangle } from "lucide-react";

interface ErrorMessageProps {
  message: string;
  className?: string;
}

export function ErrorMessage({ message, className = "" }: ErrorMessageProps) {
  return (
    <div
      className={`flex items-center justify-center p-4 text-destructive ${className}`}
      role="alert"
      data-testid="error-message"
    >
      <div className="flex items-center space-x-2">
        <AlertTriangle className="h-5 w-5" />
        <span>{message}</span>
      </div>
    </div>
  );
}
