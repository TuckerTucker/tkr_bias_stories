// lib/sorting/types.ts
export enum SortCriteria {
  ORIGINAL_ORDER = 'originalOrder', // Add original order option
  TITLE = 'title',
  RESPONSE_STATUS = 'responseStatus',
  GENERATION_DATE = 'generationDate'
}

export type SortDirection = 'asc' | 'desc';

export interface SortConfig {
  primary: SortCriteria;
  direction: SortDirection;
  // Add reference to original order
  preserveOriginalOrder?: boolean;
}

// New interface to track original order
export interface OrderedStory {
  id: string;
  originalIndex: number;
}
