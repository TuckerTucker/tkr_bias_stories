# stories/response_handlers/anthropic_handler.py
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

from tkr_utils import setup_logging, logs_and_exceptions
from tkr_utils.helper_anthropic.models import APIResponse
from stories.models import StoryResponse
from stories.story_manager import StoryManager

logger = setup_logging(__file__)

class AnthropicResponseHandler:
    """Handles Anthropic response processing and storage for stories."""

    def __init__(self, output_dir: Path) -> None:
        """Initialize the handler with output directory."""
        self.output_dir = Path(output_dir)
        self.story_manager = StoryManager()
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
            # Validate inputs
            if not response or not hasattr(response, 'content'):
                raise ValueError("Invalid Anthropic response: missing content")
            if not story_name:
                raise ValueError("story_name cannot be None or empty")
            if not hero_name:
                raise ValueError("hero_name cannot be None or empty")
            if not model:
                raise ValueError("model cannot be None or empty")

            # Extract metadata from response
            metadata = getattr(response, 'metadata', {}).copy()
            metadata.update({
                'provider': 'anthropic',
                'model': model,
                'total_tokens': response.metadata.get('usage', {}).get('total_tokens', 0) if response.metadata else 0,
                'input_tokens': response.metadata.get('usage', {}).get('input_tokens', 0) if response.metadata else 0,
                'output_tokens': response.metadata.get('usage', {}).get('output_tokens', 0) if response.metadata else 0,
                'generated_at': datetime.now().isoformat()
            })

            # Create standardized response
            return StoryResponse(
                story_id=story_name,
                hero=hero_name,
                text=response.content,
                metadata=metadata
            )
        except Exception as e:
            logger.error(f"Error formatting Anthropic response: {str(e)}")
            raise

    @logs_and_exceptions(logger)
    async def save_response(
        self,
        response: StoryResponse,
        story_name: str
    ) -> Path:
        """Save a StoryResponse to disk.

        Args:
            response: StoryResponse to save
            story_name: Name of the story

        Returns:
            Path: Path where response was saved
        """
        try:
            # Validate inputs
            if not response:
                raise ValueError("response cannot be None")
            if not story_name:
                raise ValueError("story_name cannot be None or empty")
            if not response.hero:
                raise ValueError("response.hero cannot be None or empty")

            # Create output directory if it doesn't exist
            output_dir = self.output_dir / story_name / 'anthropic'
            output_dir.mkdir(parents=True, exist_ok=True)

            # Format hero name for filename
            formatted_hero = self.story_manager.format_story_name({"story": {"title": response.hero}})
            if not formatted_hero:
                raise ValueError(f"Failed to format hero name: {response.hero}")

            output_path = output_dir / f"response_{formatted_hero}.json"

            # Convert to dict while preserving all metadata
            response_dict = response.to_dict()
            
            # Ensure metadata exists and has all required fields
            if 'metadata' not in response_dict:
                response_dict['metadata'] = {}

            # Save response to file
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(response_dict, f, indent=2, ensure_ascii=False)

            logger.info(f"Successfully saved Anthropic response to {output_path}")
            return output_path

        except Exception as e:
            logger.error(f"Error saving Anthropic response: {str(e)}")
            raise

    @logs_and_exceptions(logger)
    async def load_response(self, response_path: Path) -> StoryResponse:
        """Load a StoryResponse from disk.

        Args:
            response_path: Path to the response file

        Returns:
            StoryResponse: Loaded response object
        """
        try:
            # Validate input
            if not response_path or not response_path.exists():
                raise ValueError(f"Invalid response path: {response_path}")

            # Load response from file
            with open(response_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Ensure metadata is preserved
            if 'metadata' not in data:
                data['metadata'] = {}
            
            # Create StoryResponse from loaded data
            return StoryResponse(
                story_id=data['story_id'],
                hero=data['hero'],
                text=data['text'],
                metadata=data['metadata'],
                generated_at=datetime.fromisoformat(data.get('generated_at', datetime.now().isoformat()))
            )

        except Exception as e:
            logger.error(f"Error loading Anthropic response: {str(e)}")
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
