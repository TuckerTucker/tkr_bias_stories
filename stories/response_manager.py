# stories/response_manager.py
import json
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime
from tkr_utils.app_paths import AppPaths
from tkr_utils.config_logging import setup_logging
from tkr_utils.decorators import logs_and_exceptions
from .models import StoryResponse

logger = setup_logging(__file__)

class ResponseManager:
    """Manages reading and organizing story response data"""

    def __init__(self) -> None:
        """Initialize with base directory from AppPaths"""
        self.base_dir = AppPaths.LOCAL_DATA
        logger.info(f"Initialized ResponseManager with base directory: {self.base_dir}")

    @logs_and_exceptions(logger)
    def get_story_responses(self, story_title: str) -> Dict[str, List[StoryResponse]]:
        """
        Get all responses for a specific story.

        Args:
            story_title (str): Name of the story directory

        Returns:
            Dict with provider responses as StoryResponse objects
        """
        story_dir = self.base_dir / story_title
        if not story_dir.exists():
            logger.warning(f"Story directory not found: {story_dir}")
            return {}

        return {
            "anthropic": self._read_provider_responses(story_dir / "anthropic", story_title),
            "openai": self._read_provider_responses(story_dir / "openai", story_title)
        }

    @logs_and_exceptions(logger)
    def _read_provider_responses(self, provider_dir: Path, story_id: str) -> List[StoryResponse]:
        """
        Read all response files for a provider, maintaining original hero order.

        Args:
            provider_dir (Path): Path to provider directory
            story_id (str): ID of the story

        Returns:
            List of StoryResponse objects in original hero order
        """
        if not provider_dir.exists():
            logger.warning(f"Provider directory not found: {provider_dir}")
            return []

        # First, collect all responses with their hero names
        responses_by_hero = {}
        for response_file in provider_dir.glob("response_*.json"):
            try:
                with open(response_file) as f:
                    response_data = json.load(f)

                # Extract hero name from response data
                hero = response_data.get('hero', '')
                if hero:
                    if "anthropic" in str(provider_dir):
                        response = StoryResponse.from_anthropic(story_id, hero, response_data)
                    else:
                        response = StoryResponse.from_openai(story_id, hero, response_data)
                    responses_by_hero[hero] = response

            except Exception as e:
                logger.error(f"Error reading response file {response_file}: {str(e)}")

        return list(responses_by_hero.values())

    @logs_and_exceptions(logger)
    def combine_story_data(self, story_outline: Dict, responses: Dict[str, List[StoryResponse]]) -> Dict:
        """
        Combine story outline with response data, maintaining hero order from outline.

        Args:
            story_outline: Original story outline with ordered hero array
            responses: Dictionary of responses by provider

        Returns:
            Combined story data with responses ordered by original hero array
        """
        # Create a map of hero name to responses for each provider
        response_maps = {
            provider: {r.hero: r.to_dict() for r in resp_list}
            for provider, resp_list in responses.items()
        }

        # Order responses according to hero array
        ordered_responses = {
            provider: [
                response_maps[provider].get(hero, None)
                for hero in story_outline["hero"]
                if response_maps[provider].get(hero) is not None
            ]
            for provider in response_maps
        }

        return {
            "id": story_outline["id"],
            "title": story_outline["title"],
            "plot": story_outline.get("plot", ""),
            "hero": story_outline.get("hero", []),  # Original ordered array
            "responses": ordered_responses
        }
