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
        Read all response files for a provider.

        Args:
            provider_dir (Path): Path to provider directory
            story_id (str): ID of the story

        Returns:
            List of StoryResponse objects
        """
        if not provider_dir.exists():
            logger.warning(f"Provider directory not found: {provider_dir}")
            return []

        responses = []
        for response_file in provider_dir.glob("response_*.json"):
            try:
                with open(response_file) as f:
                    response_data = json.load(f)

                # Extract hero name from filename
                hero = response_file.stem.replace("response_", "").replace("_", " ")

                # Convert to StoryResponse based on provider
                if "anthropic" in str(provider_dir):
                    response = StoryResponse.from_anthropic(story_id, hero, response_data)
                else:
                    response = StoryResponse.from_openai(story_id, hero, response_data)

                responses.append(response)

            except Exception as e:
                logger.error(f"Error reading response file {response_file}: {str(e)}")

        return responses

    @logs_and_exceptions(logger)
    def combine_story_data(self, story_outline: Dict, responses: Dict[str, List[StoryResponse]]) -> Dict:
        """
        Combine story outline with response data.

        Args:
            story_outline (Dict): Basic story data from StoryManager
            responses (Dict[str, List[StoryResponse]]): Response data by provider

        Returns:
            Complete story data for UI
        """
        # Convert StoryResponses to dict format
        formatted_responses = {
            provider: [r.to_dict() for r in resp_list]
            for provider, resp_list in responses.items()
        }

        return {
            "id": story_outline["id"],
            "title": story_outline["title"],
            "plot": story_outline.get("plot", ""),
            "hero": story_outline.get("hero", []),
            "responses": formatted_responses
        }
