# stories/story_generator.py

import json
import os
import asyncio
from dataclasses import dataclass
from typing import List, Dict, Any, Optional
from datetime import datetime
from pathlib import Path

from tkr_utils.config_logging import setup_logging
from tkr_utils.decorators import logs_and_exceptions
from tkr_utils.helper_openai import OpenAIHelper
from tkr_utils.helper_anthropic.client import AnthropicHelper
from tkr_utils.helper_anthropic.models import RateLimits, APIResponse
from tkr_utils.helper_anthropic.processor import RequestProcessor
from tkr_utils.app_paths import AppPaths
from tkr_utils.config import (
    ANTHROPIC_API_KEY,
    ANTHROPIC_MODEL,
    MAX_REQUESTS_PER_MINUTE,
    MAX_TOKENS_PER_MINUTE
)

from stories.story_manager import StoryManager
from stories.models import StoryResponse
from prompts.prompt_manager import PromptManager
from stories.response_handlers import AnthropicResponseHandler, OpenAIResponseHandler

logger = setup_logging(__file__)

@dataclass
class GenerationStats:
    """Statistics for story generation runs"""
    total_attempted: int = 0
    existing_skipped: int = 0
    successfully_generated: int = 0
    failed: int = 0

    def to_dict(self) -> Dict[str, int]:
        """Convert stats to dictionary format"""
        return {
            "total_attempted": self.total_attempted,
            "existing_skipped": self.existing_skipped,
            "successfully_generated": self.successfully_generated,
            "failed": self.failed
        }

class StoryGenerationApp:
    """Main application orchestrator for story generation."""

    def __init__(self) -> None:
        """Initialize application components."""
        # Initialize common components
        self.story_manager = StoryManager()
        self.prompt_manager = PromptManager()
        self.output_dir = AppPaths.LOCAL_DATA

        # Initialize providers and handlers
        self.llm_openai = OpenAIHelper(async_mode=True)
        self.openai_handler = OpenAIResponseHandler(self.output_dir)

        # Initialize Anthropic components
        if not ANTHROPIC_API_KEY:
            raise ValueError("ANTHROPIC_API_KEY environment variable is required")

        self.rate_limits = RateLimits(
            requests_per_minute=int(MAX_REQUESTS_PER_MINUTE),
            tokens_per_minute=int(MAX_TOKENS_PER_MINUTE)
        )

        self.anthropic_client = AnthropicHelper(
            api_key=ANTHROPIC_API_KEY,
            model=ANTHROPIC_MODEL
        )
        self.anthropic_processor = RequestProcessor(
            client=self.anthropic_client,
            rate_limits=self.rate_limits
        )
        self.anthropic_handler = AnthropicResponseHandler(self.output_dir)

        logger.info("Initialized StoryGenerationApp with OpenAI and Anthropic processing")

    @logs_and_exceptions(logger)
    async def generate_single_story_openai(
        self,
        story_name: str,
        hero_name: str
    ) -> Dict[str, Any]:
        """Generate a single story variation with OpenAI, or return existing if found.

        Args:
            story_name: Name of the story file
            hero_name: Name of the hero character

        Returns:
            Dict[str, Any]: Story response data
        """
        try:
            # Load story data and get formatted name
            story_path = f"{self.story_manager.story_dir}/{story_name}"
            story_data = await self.story_manager.load_story(story_path)
            formatted_name = self.story_manager.format_story_name(story_data)

            # Check for existing response
            response_path = self.output_dir / formatted_name / 'openai' / f"response_{hero_name.lower().replace(' ', '_')}.json"
            if response_path.exists():
                logger.info(f"Found existing OpenAI response for {hero_name} in {story_name}")
                with open(response_path, 'r') as f:
                    return json.load(f)

            # If no existing response, generate new one
            logger.info(f"Generating new OpenAI response for {hero_name} in {story_name}")
            prompt_path = await self.prompt_manager.generate_and_save_prompt(
                story_data,
                hero_name
            )

            with open(prompt_path, 'r') as f:
                prompt = f.read()

            # Prepare and send messages
            messages = [{"role": "user", "content": prompt}]
            response = await self.llm_openai.send_message_async(messages=messages)

            # Process and save response
            response_path = await self.openai_handler.process_and_save_response(
                response=response,
                story_name=formatted_name,
                hero_name=hero_name,
                model=self.llm_openai.model
            )

            # Load and return saved response
            with open(response_path, 'r') as f:
                return json.load(f)

        except Exception as e:
            logger.error(f"Error in generate_single_story_openai for {hero_name} in {story_name}: {str(e)}")
            raise

    @logs_and_exceptions(logger)
    async def generate_single_story_anthropic(
        self,
        story_name: str,
        hero_name: str
    ) -> Dict[str, Any]:
        """Generate a single story variation with Anthropic, or return existing if found.

        Args:
            story_name: Name of the story file
            hero_name: Name of the hero character

        Returns:
            Dict[str, Any]: Story response data
        """
        try:
            # Load story data and get formatted name
            story_path = f"{self.story_manager.story_dir}/{story_name}"
            story_data = await self.story_manager.load_story(story_path)
            formatted_name = self.story_manager.format_story_name(story_data)

            # Check for existing response
            response_path = self.output_dir / formatted_name / 'anthropic' / f"response_{hero_name.lower().replace(' ', '_')}.json"
            if response_path.exists():
                logger.info(f"Found existing Anthropic response for {hero_name} in {story_name}")
                with open(response_path, 'r') as f:
                    return json.load(f)

            # If no existing response, generate new one
            logger.info(f"Generating new Anthropic response for {hero_name} in {story_name}")
            prompt_path = await self.prompt_manager.generate_and_save_prompt(
                story_data,
                hero_name
            )

            with open(prompt_path, 'r') as f:
                prompt = f.read()

            # Create request and process
            request = {"content": prompt}
            response = await self.anthropic_processor._process_single_request(request)

            # Process and save response
            response_path = await self.anthropic_handler.process_and_save_response(
                response=response,
                story_name=formatted_name,
                hero_name=hero_name,
                model=self.anthropic_client.model
            )

            # Load and return saved response
            with open(response_path, 'r') as f:
                return json.load(f)

        except Exception as e:
            logger.error(f"Error in generate_single_story_anthropic for {hero_name} in {story_name}: {str(e)}")
            raise

    @logs_and_exceptions(logger)
    async def generate_all_variations_openai(
        self,
        story_name: str
    ) -> List[Dict[str, Any]]:
        """Generate stories for all hero variants using OpenAI.

        Args:
            story_name: Name of the story file

        Returns:
            List of standardized story responses
        """
        try:
            # Load story data
            story_path = f"{self.story_manager.story_dir}/{story_name}"
            story_data = await self.story_manager.load_story(story_path)

            # Create tasks for each hero
            tasks = []
            for hero in story_data['story']['hero']:
                task = self.generate_single_story_openai(story_name, hero)
                tasks.append(task)

            # Execute all tasks concurrently
            responses = await asyncio.gather(*tasks, return_exceptions=True)

            # Filter out exceptions and log them
            valid_responses = []
            for i, response in enumerate(responses):
                if isinstance(response, Exception):
                    hero = story_data['story']['hero'][i]
                    logger.error(f"Error generating OpenAI story for {hero}: {str(response)}")
                else:
                    valid_responses.append(response)

            logger.info(
                f"Successfully generated {len(valid_responses)} OpenAI variations "
                f"for {story_name} (Failed: {len(responses) - len(valid_responses)})"
            )
            return valid_responses

        except Exception as e:
            logger.error(f"Error generating OpenAI story variations: {str(e)}")
            raise

    @logs_and_exceptions(logger)
    async def generate_all_variations_anthropic(
        self,
        story_name: str
    ) -> List[Dict[str, Any]]:
        """Generate stories for all hero variants using Anthropic.

        Args:
            story_name: Name of the story file

        Returns:
            List of standardized story responses
        """
        try:
            story_path = f"{self.story_manager.story_dir}/{story_name}"
            story_data = await self.story_manager.load_story(story_path)

            tasks = []
            for hero in story_data['story']['hero']:
                task = self.generate_single_story_anthropic(story_name, hero)
                tasks.append(task)

            responses = await asyncio.gather(*tasks)
            logger.info(f"Successfully generated all Anthropic variations for {story_name}")
            return responses

        except Exception as e:
            logger.error(f"Error generating Anthropic story variations: {str(e)}")
            raise

    async def list_available_stories(self) -> List[Dict[str, str]]:
        """Get list of all available stories."""
        try:
            stories = self.story_manager.get_all_stories()
            logger.info(f"Found {len(stories)} available stories")
            return stories
        except Exception as e:
            logger.error(f"Error listing stories: {str(e)}")
            raise

async def main(story_name: Optional[str] = None):
    """Main entry point for story generation.

    Args:
        story_name: Optional specific story to generate. If None, generates all stories.
    """
    try:
        app = StoryGenerationApp()
        stats = GenerationStats()

        # List available stories
        stories = await app.list_available_stories()
        logger.info("Available stories:")
        for story in stories:
            logger.info(f"- {story['title']}")

        # Determine which stories to process
        stories_to_process = (
            [s for s in stories if s['id'] == story_name] if story_name
            else stories
        )

        if not stories_to_process:
            logger.error(f"No stories found{' matching ' + story_name if story_name else ''}")
            return

        all_responses = {}

        # Process each story
        for story in stories_to_process:
            story_id = story['id']
            logger.info(f"Processing story: {story['title']}")

            # Create tasks for both providers
            openai_task = app.generate_all_variations_openai(f"{story_id}.json")
            anthropic_task = app.generate_all_variations_anthropic(f"{story_id}.json")

            try:
                # Run both tasks concurrently
                results = await asyncio.gather(
                    openai_task,
                    anthropic_task,
                    return_exceptions=True
                )

                openai_responses, anthropic_responses = results

                # Update statistics and store responses
                stats.total_attempted += len(story['hero']) * 2  # Both providers

                for responses, provider in [
                    (openai_responses, "openai"),
                    (anthropic_responses, "anthropic")
                ]:
                    if isinstance(responses, Exception):
                        logger.error(f"Error in {provider} generation for {story_id}: {str(responses)}")
                        stats.failed += len(story['hero'])
                        responses = []
                    else:
                        # Count existing vs new responses
                        existing_count = sum(1 for r in responses if r.get('metadata', {}).get('existing', False))
                        stats.existing_skipped += existing_count
                        stats.successfully_generated += len(responses) - existing_count

                all_responses[story_id] = {
                    "openai": [] if isinstance(openai_responses, Exception) else openai_responses,
                    "anthropic": [] if isinstance(anthropic_responses, Exception) else anthropic_responses
                }

            except Exception as e:
                logger.error(f"Error processing story {story_id}: {str(e)}")
                stats.failed += len(story['hero']) * 2  # Both providers
                continue

        # Log final statistics
        logger.info("Generation Statistics:")
        for key, value in stats.to_dict().items():
            logger.info(f"  {key}: {value}")

        return all_responses

    except Exception as e:
        logger.error(f"Application error: {str(e)}")
        raise

if __name__ == "__main__":
    import sys

    # Get optional story name from command line
    story_name = sys.argv[1] if len(sys.argv) > 1 else None

    asyncio.run(main(story_name))
