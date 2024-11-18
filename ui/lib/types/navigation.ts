// lib/types/navigation.ts
export interface HeroNavigation {
  storyId: string;
  provider: string;
  heroName: string;
}

export interface ScrollConfig {
  behavior: ScrollBehavior;
  offset?: number;
  scrollTop?: number;
}

export interface NavigationState {
  selectedHero: HeroNavigation | null;
  activeProvider: string | null;
  scrollPositions: Map<string, number>;
}

export interface NavigationContextType {
  selectedHero: HeroNavigation | null;
  activeProvider: string | null;
  selectHero: (nav: HeroNavigation) => void;
  setProvider: (provider: string) => void;
  clearSelection: () => void;
  saveScrollPosition: (heroId: string, position: number) => void;
  getScrollPosition: (heroId: string) => number;
}
