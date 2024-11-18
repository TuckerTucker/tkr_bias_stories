// lib/hooks/use-story-sorting.ts
import { useState, useCallback, useEffect } from 'react';
import { Story } from '../api/types';
import { SortConfig, SortCriteria } from '../sorting/types';
import { createSortFunction } from '../sorting/utils';

const SORT_PREFERENCES_KEY = 'story-sort-preferences';

const defaultConfig: SortConfig = {
  primary: SortCriteria.ORIGINAL_ORDER, // Changed default to original order
  direction: 'asc',
  preserveOriginalOrder: true
};

export function useStorySorting(stories: Story[]) {
  const [sortConfig, setSortConfig] = useState<SortConfig>(defaultConfig);
  const [sortedStories, setSortedStories] = useState<Story[]>(stories);
  const [originalHeroOrder, setOriginalHeroOrder] = useState<string[]>([]);

  // Initialize original order from first story's hero array
  useEffect(() => {
    if (stories.length > 0 && stories[0].hero) {
      setOriginalHeroOrder(stories[0].hero);
    }
  }, [stories]);

  // Load saved preferences
  useEffect(() => {
    const savedPrefs = localStorage.getItem(SORT_PREFERENCES_KEY);
    if (savedPrefs) {
      try {
        const { config } = JSON.parse(savedPrefs);
        setSortConfig(config);
      } catch (e) {
        console.error('Error loading sort preferences:', e);
      }
    }
  }, []);

  // Save preferences when config changes
  useEffect(() => {
    const prefs = {
      config: sortConfig,
      lastUpdated: new Date().toISOString()
    };
    localStorage.setItem(SORT_PREFERENCES_KEY, JSON.stringify(prefs));
  }, [sortConfig]);

  // Sort stories when config or stories change
  useEffect(() => {
    if (originalHeroOrder.length === 0) return;

    const sortFn = createSortFunction(sortConfig, originalHeroOrder);
    const sorted = [...stories].sort(sortFn);
    setSortedStories(sorted);
  }, [stories, sortConfig, originalHeroOrder]);

  const updateSort = useCallback((updates: Partial<SortConfig>) => {
    setSortConfig(current => ({
      ...current,
      ...updates
    }));
  }, []);

  const toggleDirection = useCallback(() => {
    setSortConfig(current => ({
      ...current,
      direction: current.direction === 'asc' ? 'desc' : 'asc'
    }));
  }, []);

  const resetSort = useCallback(() => {
    setSortConfig(defaultConfig);
  }, []);

  return {
    sortConfig,
    sortedStories,
    updateSort,
    toggleDirection,
    resetSort,
    originalHeroOrder
  };
}
