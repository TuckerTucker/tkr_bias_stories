// lib/sorting/utils.ts
import { Story } from "../api/types";
import { SortCriteria, SortConfig } from "./types";

export const hasResponses = (story: Story): boolean => {
  return Object.values(story.responses).some(responses => responses.length > 0);
};

export const getLatestGenerationDate = (story: Story): Date => {
  let latest = new Date(0);
  Object.values(story.responses).forEach(responses => {
    responses.forEach(response => {
      const date = new Date(response.metadata.generated_at);
      if (date > latest) latest = date;
    });
  });
  return latest;
};

// New function to maintain original order when other criteria are equal
export const compareOriginalOrder = (a: Story, b: Story, heroOrder: string[]): number => {
  const aIndex = heroOrder.indexOf(a.hero[0]);
  const bIndex = heroOrder.indexOf(b.hero[0]);
  return aIndex - bIndex;
};

export const createSortFunctionForCriteria = (criteria: SortCriteria, heroOrder: string[]) => {
  switch (criteria) {
    case SortCriteria.ORIGINAL_ORDER:
      return (a: Story, b: Story) => compareOriginalOrder(a, b, heroOrder);

    case SortCriteria.TITLE:
      return (a: Story, b: Story) => {
        const titleCompare = a.title.localeCompare(b.title);
        return titleCompare === 0 ? compareOriginalOrder(a, b, heroOrder) : titleCompare;
      };

    case SortCriteria.RESPONSE_STATUS:
      return (a: Story, b: Story) => {
        const aHasResponses = hasResponses(a);
        const bHasResponses = hasResponses(b);
        const statusCompare = aHasResponses === bHasResponses ? 0 : aHasResponses ? -1 : 1;
        return statusCompare === 0 ? compareOriginalOrder(a, b, heroOrder) : statusCompare;
      };

    case SortCriteria.GENERATION_DATE:
      return (a: Story, b: Story) => {
        const aDate = getLatestGenerationDate(a);
        const bDate = getLatestGenerationDate(b);
        const dateCompare = bDate.getTime() - aDate.getTime();
        return dateCompare === 0 ? compareOriginalOrder(a, b, heroOrder) : dateCompare;
      };

    default:
      return (a: Story, b: Story) => compareOriginalOrder(a, b, heroOrder);
  }
};

export const applySortDirection = (
  comparison: number,
  direction: 'asc' | 'desc',
  criteria: SortCriteria
): number => {
  // Always maintain original order for ORIGINAL_ORDER regardless of direction
  if (criteria === SortCriteria.ORIGINAL_ORDER) {
    return comparison;
  }
  return direction === 'asc' ? comparison : -comparison;
};

export const createSortFunction = (config: SortConfig, heroOrder: string[]) => {
  const sortFn = createSortFunctionForCriteria(config.primary, heroOrder);

  return (a: Story, b: Story): number => {
    return applySortDirection(sortFn(a, b), config.direction, config.primary);
  };
};
