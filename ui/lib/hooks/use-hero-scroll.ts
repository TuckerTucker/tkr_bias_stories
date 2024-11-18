// lib/hooks/use-hero-scroll.ts
import { useEffect, useRef } from 'react';
import { useNavigation } from '@/lib/context/navigation-context';
import { generateHeroId, scrollToElement } from '@/lib/utils/navigation';

export function useHeroScroll(storyId: string) {
  const { selectedHero } = useNavigation();
  const scrollTimeoutRef = useRef<NodeJS.Timeout>();

  useEffect(() => {
    if (selectedHero && selectedHero.storyId === storyId) {
      // Clear any existing timeout
      if (scrollTimeoutRef.current) {
        clearTimeout(scrollTimeoutRef.current);
      }

      // Add a small delay to ensure DOM is ready
      scrollTimeoutRef.current = setTimeout(() => {
        const heroId = generateHeroId(
          selectedHero.storyId,
          selectedHero.provider,
          selectedHero.heroName
        );
        scrollToElement(heroId);
      }, 100);
    }

    return () => {
      if (scrollTimeoutRef.current) {
        clearTimeout(scrollTimeoutRef.current);
      }
    };
  }, [selectedHero, storyId]);
}
