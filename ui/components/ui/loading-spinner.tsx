"use client";
// ui/components/ui/loading-spinner.tsx
export function LoadingSpinner() {
  return (
    <div
      data-testid="loading-spinner"
      className="flex items-center justify-center p-4"
    >
      <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
    </div>
  );
}
