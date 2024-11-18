# stories/response_handlers/openai_handler.py
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

from tkr_utils import setup_logging, logs_and_exceptions
from stories.models import StoryResponse

logger = setup_logging(__file__)

class OpenAIResponseHandler:
    """Handles OpenAI response processing and storage for stories."""

    def __init__(self, output_dir: Path) -> None:
        """Initialize the handler with output directory."""
        self.output_dir = Path(output_dir)
        logger.info(f"Initialized OpenAIResponseHandler with output dir: {self.output_dir}")

    @logs_and_exceptions(logger)
    async def format_response(
        self,
        response: Dict[str, Any],
        story_name: str,
        hero_name: str,
        model: str
    ) -> StoryResponse:
        """Format OpenAI response into standardized StoryResponse.

        Args:
            response: Raw OpenAI API response
            story_name: Name of the story
            hero_name: Name of the hero character
            model: Model identifier used

        Returns:
            StoryResponse: Formatted response object
        """
        try:
            # Extract content and usage from OpenAI response
            content = response.choices[0].message.content
            usage = response.usage.model_dump()

            # Create standardized response
            return StoryResponse(
                story_id=story_name,
                hero=hero_name,
                text=content,  # Now directly using content as text
                metadata={
                    'provider': 'openai',
                    'model': model,
                    'total_tokens': usage['total_tokens'],
                    'input_tokens': usage['prompt_tokens'],
                    'output_tokens': usage['completion_tokens'],
                    'generated_at': datetime.now().isoformat()
                }
            )
        except Exception as e:
            logger.error(f"Error formatting OpenAI response: {str(e)}")
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
            story_dir = self.output_dir / story_name / 'openai'
            story_dir.mkdir(parents=True, exist_ok=True)

            # Create filename from hero name
            hero_filename = f"response_{response.hero.lower().replace(' ', '_')}.json"
            response_path = story_dir / hero_filename

            # Save response
            with open(response_path, 'w', encoding='utf-8') as f:
                json.dump(response.to_dict(), f, indent=2, ensure_ascii=False)

            logger.info(f"Successfully saved OpenAI response to {response_path}")
            return response_path

        except Exception as e:
            logger.error(f"Error saving OpenAI response: {str(e)}")
            raise

    @logs_and_exceptions(logger)
    async def process_and_save_response(
        self,
        response: Dict[str, Any],
        story_name: str,
        hero_name: str,
        model: str
    ) -> Path:
        """Format and save response in one operation.

        Args:
            response: Raw OpenAI response
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
