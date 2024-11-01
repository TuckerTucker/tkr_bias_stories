import json
from pathlib import Path
from typing import Dict, List, Optional
from tkr_utils.app_paths import AppPaths
from tkr_utils.config_logging import setup_logging
from tkr_utils.decorators import logs_and_exceptions

logger = setup_logging(__file__)

class ResponseManager:
    """Manages reading and organizing story response data"""

    def __init__(self) -> None:
        """Initialize with base directory from AppPaths"""
        self.base_dir = AppPaths.LOCAL_DATA
        logger.info(f"Initialized ResponseManager with base directory: {self.base_dir}")

    @logs_and_exceptions(logger)
    def get_story_responses(self, story_title: str) -> Dict:
        """
        Get all responses for a specific story.

        Args:
            story_title (str): Name of the story directory

        Returns:
            Dict with provider responses
        """
        story_dir = self.base_dir / story_title
        if not story_dir.exists():
            logger.warning(f"Story directory not found: {story_dir}")
            return {}

        return {
            "anthropic": self._read_provider_responses(story_dir / "anthropic"),
            "openai": self._read_provider_responses(story_dir / "openai")
        }

    @logs_and_exceptions(logger)
    def _read_provider_responses(self, provider_dir: Path) -> List[Dict]:
        """
        Read all response files for a provider.

        Args:
            provider_dir (Path): Path to provider directory

        Returns:
            List of response data dictionaries
        """
        if not provider_dir.exists():
            logger.warning(f"Provider directory not found: {provider_dir}")
            return []

        responses = []
        for response_file in provider_dir.glob("response_*.json"):
            try:
                with open(response_file) as f:
                    response_data = json.load(f)
                    responses.append(response_data)
            except Exception as e:
                logger.error(f"Error reading response file {response_file}: {str(e)}")

        return responses

    @logs_and_exceptions(logger)
    def combine_story_data(self, story_outline: Dict, responses: Dict) -> Dict:
        """
        Combine story outline with response data.

        Args:
            story_outline (Dict): Basic story data from StoryManager
            responses (Dict): Response data by provider

        Returns:
            Complete story data for UI
        """
        return {
            "id": story_outline["id"],
            "title": story_outline["title"],
            "plot": story_outline.get("plot", ""),
            "hero": story_outline.get("hero", []),
            "responses": responses
        }
