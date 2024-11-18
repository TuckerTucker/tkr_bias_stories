// components/ui/scroll-position-tracker.tsx
"use client";

import { useEffect } from 'react';
import { useNavigation } from '@/lib/context/navigation-context';
import { generateHeroId } from '@/lib/utils/navigation';

interface ScrollPositionTrackerProps {
  storyId: string;
  heroName: string;
}

export function ScrollPositionTracker({ storyId, heroName }: ScrollPositionTrackerProps) {
  const { activeProvider, saveScrollPosition } = useNavigation();

  useEffect(() => {
    if (!activeProvider) return;

    const heroId = generateHeroId(storyId, activeProvider, heroName);
    let timeoutId: NodeJS.Timeout;

    const handleScroll = () => {
      // Debounce scroll handler
      clearTimeout(timeoutId);
      timeoutId = setTimeout(() => {
        saveScrollPosition(heroId, window.scrollY);
      }, 100);
    };

    window.addEventListener('scroll', handleScroll);
    return () => {
      window.removeEventListener('scroll', handleScroll);
      clearTimeout(timeoutId);
    };
  }, [storyId, heroName, activeProvider, saveScrollPosition]);

  return null;
}
