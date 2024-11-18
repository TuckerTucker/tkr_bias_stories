// components/ui/hero-item.tsx
import { useNavigation } from '@/lib/context/navigation-context';
import { generateHeroId } from '@/lib/utils/navigation';
import { cn } from '@/lib/utils';

interface HeroItemProps {
  storyId: string;
  heroName: string;
  index: number;
}

export function HeroItem({ storyId, heroName, index }: HeroItemProps) {
  const { selectedHero, activeProvider, selectHero } = useNavigation();

  // Check if this hero is currently selected
  const isSelected = selectedHero?.heroName === heroName &&
                    selectedHero?.storyId === storyId &&
                    selectedHero?.provider === (activeProvider || 'anthropic');

  const handleSelect = () => {
    // Default to 'anthropic' if no provider is active
    const provider = activeProvider || 'anthropic';
    selectHero({
      storyId,
      provider,
      heroName
    });
  };

  // Generate consistent ID for scroll targeting
  const heroId = generateHeroId(
    storyId,
    activeProvider || 'anthropic',
    heroName
  );

  return (
    <li
      id={heroId}
      className={cn(
        // Base styles
        "truncate px-2 py-1 rounded-md cursor-pointer transition-all",
        // Interactive states
        "hover:bg-accent hover:text-accent-foreground",
        "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring",
        "active:scale-[0.98]",
        // Selection state
        isSelected && "bg-accent text-accent-foreground"
      )}
      role="option" // Change from button to option
      tabIndex={0}
      onClick={handleSelect}
      onKeyDown={(e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault();
          handleSelect();
        }
      }}
      data-testid={`hero-${storyId}-${index}`}
      aria-selected={isSelected} // Now valid with role="option"
      aria-label={`Select hero: ${heroName}`}
    >
      {heroName}
    </li>
  );
}
