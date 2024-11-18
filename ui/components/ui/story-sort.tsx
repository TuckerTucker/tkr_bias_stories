// components/ui/story-sort.tsx
"use client";

import { Button } from "@/components/ui/button";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { SortAscIcon, SortDescIcon, RotateCcwIcon } from "lucide-react";
import { SortConfig, SortCriteria } from "@/lib/sorting/types";

const SORT_OPTIONS = [
  { value: SortCriteria.ORIGINAL_ORDER, label: 'Original Order' },
  { value: SortCriteria.TITLE, label: 'Title' },
  { value: SortCriteria.RESPONSE_STATUS, label: 'Response Status' },
  { value: SortCriteria.GENERATION_DATE, label: 'Generation Date' },
] as const;

interface StorySortProps {
  config: SortConfig;
  onUpdateSort: (updates: Partial<SortConfig>) => void;
  onToggleDirection: () => void;
  onReset: () => void;
  disableDirection?: boolean;
}

export function StorySort({
  config,
  onUpdateSort,
  onToggleDirection,
  onReset,
  disableDirection = false
}: StorySortProps) {
  const isOriginalOrder = config.primary === SortCriteria.ORIGINAL_ORDER;

  return (
    <div className="flex items-center gap-2 p-2">
      <Select
        value={config.primary}
        onValueChange={(value: SortCriteria) =>
          onUpdateSort({ primary: value })}
      >
        <SelectTrigger className="w-[180px]">
          <SelectValue placeholder="Sort by..." />
        </SelectTrigger>
        <SelectContent>
          {SORT_OPTIONS.map(option => (
            <SelectItem
              key={option.value}
              value={option.value}
            >
              {option.label}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>

      <Button
        variant="outline"
        size="icon"
        onClick={onToggleDirection}
        disabled={isOriginalOrder || disableDirection}
        title={`Sort ${config.direction === 'asc' ? 'Ascending' : 'Descending'}`}
        className={isOriginalOrder ? 'opacity-50' : ''}
      >
        {config.direction === 'asc' ? (
          <SortAscIcon className="h-4 w-4" />
        ) : (
          <SortDescIcon className="h-4 w-4" />
        )}
      </Button>

      <Button
        variant="ghost"
        size="icon"
        onClick={onReset}
        title="Reset to original order"
        disabled={isOriginalOrder}
      >
        <RotateCcwIcon className="h-4 w-4" />
      </Button>
    </div>
  );
}
