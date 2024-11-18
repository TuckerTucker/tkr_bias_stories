// lib/utils/navigation.ts
import { ScrollConfig } from "../types/navigation";

export const HEADER_HEIGHT = 116; // Height of sticky header + padding

export function generateHeroId(
  storyId: string,
  provider: string,
  heroName: string,
): string {
  return `hero-${storyId}-${provider}-${heroName.toLowerCase().replace(/\s+/g, "-")}`;
}

export function scrollToElement(
  elementId: string,
  config: ScrollConfig & { scrollTop?: number } = {
    behavior: "smooth",
    offset: HEADER_HEIGHT,
  }
) {
  try {
    const element = document.getElementById(elementId);
    if (!element) {
      console.warn(`Element with id ${elementId} not found`);
      return;
    }

    const scrollTop =
      config.scrollTop !== undefined
        ? config.scrollTop
        : element.getBoundingClientRect().top +
          window.pageYOffset -
          (config.offset ?? HEADER_HEIGHT);

    window.scrollTo({
      top: scrollTop,
      behavior: config.behavior || "smooth",
    });
  } catch (error) {
    console.error("Error scrolling to element:", error);
  }
}

export function findHeroElement(
  storyId: string,
  provider: string,
  heroName: string,
): HTMLElement | null {
  const id = generateHeroId(storyId, provider, heroName);
  return document.getElementById(id);
}
