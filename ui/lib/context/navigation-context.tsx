// lib/context/navigation-context.tsx
"use client";

import {
  createContext,
  useContext,
  useState,
  ReactNode,
  useEffect,
  useCallback
} from 'react';

import {
  NavigationState,
  NavigationContextType,
  HeroNavigation,
  ScrollConfig
} from '../types/navigation';
import { scrollToElement, generateHeroId } from '../utils/navigation';

const SCROLL_STORAGE_KEY = 'hero-scroll-positions';
const DEFAULT_SCROLL_CONFIG: ScrollConfig = {
  behavior: 'smooth',
  offset: 80
};

const NavigationContext = createContext<NavigationContextType | undefined>(undefined);

export function NavigationProvider({ children }: { children: ReactNode }) {
  const [state, setState] = useState<NavigationState>({
    selectedHero: null,
    activeProvider: null,
    scrollPositions: new Map<string, number>()
  });

  // Load saved scroll positions on mount
  useEffect(() => {
    const savedPositions = localStorage.getItem(SCROLL_STORAGE_KEY);
    if (savedPositions) {
      try {
        // Explicitly type the parsed data and create a properly typed Map
        const parsed = JSON.parse(savedPositions) as [string, number][];
        const positions = new Map<string, number>(parsed);

        setState(prev => ({
          ...prev,
          scrollPositions: positions
        }));
      } catch (error) {
        console.error('Error loading scroll positions:', error);
      }
    }
  }, []);

  // Save scroll positions when they change
  useEffect(() => {
    const positionsArray = Array.from(state.scrollPositions.entries());
    localStorage.setItem(SCROLL_STORAGE_KEY, JSON.stringify(positionsArray));
  }, [state.scrollPositions]);

  const saveScrollPosition = useCallback((heroId: string, position: number) => {
    setState(prev => ({
      ...prev,
      scrollPositions: new Map(prev.scrollPositions).set(heroId, position)
    }));
  }, []);

  const getScrollPosition = useCallback((heroId: string) => {
    return state.scrollPositions.get(heroId) || 0;
  }, [state.scrollPositions]);

  // Handle hero selection and scroll position
  useEffect(() => {
    if (state.selectedHero && state.activeProvider) {
      const heroId = generateHeroId(
        state.selectedHero.storyId,
        state.activeProvider,
        state.selectedHero.heroName
      );

      const frameId = requestAnimationFrame(() => {
        setTimeout(() => {
          const savedPosition = getScrollPosition(heroId);
          scrollToElement(heroId, {
            ...DEFAULT_SCROLL_CONFIG,
            scrollTop: savedPosition
          });
        }, 50);
      });

      return () => cancelAnimationFrame(frameId);
    }
  }, [state.selectedHero, state.activeProvider, getScrollPosition]);

  const selectHero = useCallback((nav: HeroNavigation) => {
    setState(prev => {
      // Save current scroll position before switching heroes
      if (prev.selectedHero && prev.activeProvider) {
        const currentHeroId = generateHeroId(
          prev.selectedHero.storyId,
          prev.activeProvider,
          prev.selectedHero.heroName
        );
        const currentScrollPositions = new Map(prev.scrollPositions);
        currentScrollPositions.set(currentHeroId, window.scrollY);

        // Toggle selection if clicking same hero
        if (
          prev.selectedHero.heroName === nav.heroName &&
          prev.selectedHero.storyId === nav.storyId &&
          prev.activeProvider === nav.provider
        ) {
          return {
            ...prev,
            selectedHero: null,
            scrollPositions: currentScrollPositions
          };
        }

        return {
          ...prev,
          selectedHero: nav,
          activeProvider: nav.provider,
          scrollPositions: currentScrollPositions
        };
      }

      return {
        ...prev,
        selectedHero: nav,
        activeProvider: nav.provider || prev.activeProvider || 'anthropic'
      };
    });
  }, []);

  const setProvider = useCallback((provider: string) => {
    setState(prev => {
      // Create new scroll positions map
      const currentScrollPositions = new Map(prev.scrollPositions);

      // Save current scroll position if we have a selected hero
      if (prev.selectedHero && prev.activeProvider) {
        const currentHeroId = generateHeroId(
          prev.selectedHero.storyId,
          prev.activeProvider,
          prev.selectedHero.heroName
        );
        currentScrollPositions.set(currentHeroId, window.scrollY);
      }

      // Always maintain the selected hero when changing providers
      const updatedState = {
        ...prev,
        activeProvider: provider,
        scrollPositions: currentScrollPositions,
      };

      // Update the hero's provider reference if we have a selected hero
      if (prev.selectedHero) {
        updatedState.selectedHero = {
          ...prev.selectedHero,
          provider // Update only the provider, maintaining story and hero selection
        };
      }

      return updatedState;
    });
  }, []);

  const clearSelection = useCallback(() => {
    setState(prev => {
      // Save current scroll position before clearing
      if (prev.selectedHero && prev.activeProvider) {
        const currentHeroId = generateHeroId(
          prev.selectedHero.storyId,
          prev.activeProvider,
          prev.selectedHero.heroName
        );
        const currentScrollPositions = new Map(prev.scrollPositions);
        currentScrollPositions.set(currentHeroId, window.scrollY);

        return {
          selectedHero: null,
          activeProvider: null,
          scrollPositions: currentScrollPositions
        };
      }

      return {
        ...prev,
        selectedHero: null,
        activeProvider: null
      };
    });
  }, []);

  const value: NavigationContextType = {
    selectedHero: state.selectedHero,
    activeProvider: state.activeProvider,
    selectHero,
    setProvider,
    clearSelection,
    saveScrollPosition,
    getScrollPosition
  };

  return (
    <NavigationContext.Provider value={value}>
      {children}
    </NavigationContext.Provider>
  );
}

export function useNavigation() {
  const context = useContext(NavigationContext);
  if (!context) {
    throw new Error('useNavigation must be used within a NavigationProvider');
  }
  return context;
}
