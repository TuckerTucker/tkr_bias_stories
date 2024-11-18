# stories/response_handlers/anthropic_handler.py
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

from tkr_utils import setup_logging, logs_and_exceptions
from tkr_utils.helper_anthropic.models import APIResponse
from stories.models import StoryResponse

logger = setup_logging(__file__)

class AnthropicResponseHandler:
    """Handles Anthropic response processing and storage for stories."""

    def __init__(self, output_dir: Path) -> None:
        """Initialize the handler with output directory."""
        self.output_dir = Path(output_dir)
        logger.info(f"Initialized AnthropicResponseHandler with output dir: {self.output_dir}")

    @logs_and_exceptions(logger)
    async def format_response(
        self,
        response: APIResponse,
        story_name: str,
        hero_name: str,
        model: str
    ) -> StoryResponse:
        """Format Anthropic response into standardized StoryResponse.

        Args:
            response: Raw APIResponse from Anthropic
            story_name: Name of the story
            hero_name: Name of the hero character
            model: Model identifier used

        Returns:
            StoryResponse: Formatted response object
        """
        try:
            # Create standardized response with plain text
            return StoryResponse(
                story_id=story_name,
                hero=hero_name,
                text=response.content,  # Now directly using content as text
                metadata={
                    'provider': 'anthropic',
                    'model': model,
                    'total_tokens': response.metadata.get('usage', {}).get('total_tokens', 0) if response.metadata else 0,
                    'generated_at': datetime.now().isoformat()
                }
            )
        except Exception as e:
            logger.error(f"Error formatting response: {str(e)}")
            raise

    @logs_and_exceptions(logger)
    async def save_response(
        self,
        response: StoryResponse,
        story_name: str
    ) -> Path:
        """Save formatted response to appropriate directory.

        Args:
            response: Formatted StoryResponse
            story_name: Name of the story

        Returns:
            Path: Path where response was saved
        """
        try:
            # Create provider-specific directory
            story_dir = self.output_dir / story_name / 'anthropic'
            story_dir.mkdir(parents=True, exist_ok=True)

            # Create filename from hero name
            hero_filename = f"response_{response.hero.lower().replace(' ', '_')}.json"
            response_path = story_dir / hero_filename

            # Save response
            with open(response_path, 'w', encoding='utf-8') as f:
                json.dump(response.to_dict(), f, indent=2, ensure_ascii=False)

            logger.info(f"Successfully saved Anthropic response to {response_path}")
            return response_path

        except Exception as e:
            logger.error(f"Error saving response: {str(e)}")
            raise

    @logs_and_exceptions(logger)
    async def process_and_save_response(
        self,
        response: APIResponse,
        story_name: str,
        hero_name: str,
        model: str
    ) -> Path:
        """Format and save response in one operation.

        Args:
            response: Raw APIResponse
            story_name: Name of the story
            hero_name: Name of the hero character
            model: Model identifier

        Returns:
            Path: Path where response was saved
        """
        formatted_response = await self.format_response(
            response=response,
            story_name=story_name,
            hero_name=hero_name,
            model=model
        )
        return await self.save_response(formatted_response, story_name)
