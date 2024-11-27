# stories/story_generator.py

import os
import json
import asyncio
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

from tkr_utils import setup_logging, logs_and_exceptions
from tkr_utils.helper_anthropic import AnthropicHelper
from tkr_utils.helper_anthropic.models import APIResponse
from tkr_utils.helper_anthropic.processor import RequestProcessor, RateLimits
from tkr_utils.helper_openai import OpenAIHelper
from stories.models import StoryResponse
from stories.story_manager import StoryManager
from prompts.prompt_manager import PromptManager
from stories.response_handlers.openai_handler import OpenAIResponseHandler
from stories.response_handlers.anthropic_handler import AnthropicResponseHandler
from stories.bias_report_generator import BiasReportGenerator
from tkr_utils.app_paths import AppPaths
from tkr_utils.config import (
    ANTHROPIC_API_KEY,
    ANTHROPIC_MODEL,
    MAX_REQUESTS_PER_MINUTE,
    MAX_TOKENS_PER_MINUTE
)

logger = setup_logging(__file__)


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

        # Initialize BiasReportGenerator with story generation methods
        self.bias_report_generator = BiasReportGenerator(
            self.story_manager,
            self.prompt_manager,
            self.generate_single_story_anthropic,
            self.generate_single_story_openai
        )

        logger.info("Initialized StoryGenerationApp with OpenAI and Anthropic processing")

    @logs_and_exceptions(logger)
    async def _check_existing_files(
        self,
        formatted_name: str,
        provider: str,
        hero_name: str
    ) -> tuple[bool, bool, bool]:
        """Check if story response and bias report already exist.

        Args:
            formatted_name: Formatted story name
            provider: Provider name (openai/anthropic)
            hero_name: Name of the hero character

        Returns:
            Tuple of (story_exists, bias_report_exists, should_process)
            where should_process indicates if we need to generate anything
        """
        formatted_hero = self.story_manager.format_story_name({"story": {"title": hero_name}})
        
        # Use Path objects for consistent path handling
        story_path = Path(self.output_dir) / formatted_name / provider / f"response_{formatted_hero}.json"
        bias_path = Path(self.output_dir) / formatted_name / provider / f"bias_report_{formatted_hero}.json"
        
        story_exists = story_path.exists()
        bias_exists = bias_path.exists()
        
        # Determine if we need to process based on the four scenarios:
        # 1. Neither exists: True (generate both)
        # 2. Response doesn't exist but bias does: True (regenerate both)
        # 3. Response exists but bias doesn't: True (generate bias)
        # 4. Both exist: False (skip)
        should_process = not (story_exists and bias_exists)
        
        return story_exists, bias_exists, should_process

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
            story_path = Path(self.story_manager.story_dir) / story_name
            story_data = await self.story_manager.load_story(story_path)
            formatted_name = self.story_manager.format_story_name(story_data)

            # Check for existing files
            story_exists, bias_exists, should_process = await self._check_existing_files(formatted_name, 'openai', hero_name)
            
            if not should_process:
                logger.info(f"Found existing OpenAI response and bias report for {hero_name} in {story_name}")
                formatted_hero = self.story_manager.format_story_name({"story": {"title": hero_name}})
                response_path = Path(self.output_dir) / formatted_name / 'openai' / f"response_{formatted_hero}.json"
                
                # Load existing response using handler
                response_data = await self.openai_handler.load_response(response_path)
                
                # Mark as existing in metadata if not already marked
                if not response_data.metadata.get('existing', False):
                    response_data.metadata['existing'] = True
                    # Save back with updated metadata
                    await self.openai_handler.save_response(response_data, formatted_name)
                
                return response_data.to_dict()

            # Generate new story response if needed
            if not story_exists or not bias_exists:
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

                # Load saved response
                response_data = await self.openai_handler.load_response(response_path)
            else:
                # Load existing response if we only need to generate bias report
                formatted_hero = self.story_manager.format_story_name({"story": {"title": hero_name}})
                response_path = Path(self.output_dir) / formatted_name / 'openai' / f"response_{formatted_hero}.json"
                response_data = await self.openai_handler.load_response(response_path)

            # Generate bias report if needed
            if not bias_exists or not story_exists:
                logger.info(f"Generating bias report for {hero_name} in {story_name}")
                story_id = os.path.splitext(story_name)[0]  # Remove .json extension
                await self.bias_report_generator.generate_bias_report(story_id)
            
            return response_data.to_dict()

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
            story_path = Path(self.story_manager.story_dir) / story_name
            story_data = await self.story_manager.load_story(story_path)
            formatted_name = self.story_manager.format_story_name(story_data)

            # Check for existing files
            story_exists, bias_exists, should_process = await self._check_existing_files(formatted_name, 'anthropic', hero_name)
            
            if not should_process:
                logger.info(f"Found existing Anthropic response and bias report for {hero_name} in {story_name}")
                formatted_hero = self.story_manager.format_story_name({"story": {"title": hero_name}})
                response_path = Path(self.output_dir) / formatted_name / 'anthropic' / f"response_{formatted_hero}.json"
                
                # Load existing response using handler
                response_data = await self.anthropic_handler.load_response(response_path)
                
                # Mark as existing in metadata if not already marked
                if not response_data.metadata.get('existing', False):
                    response_data.metadata['existing'] = True
                    # Save back with updated metadata
                    await self.anthropic_handler.save_response(response_data, formatted_name)
                
                return response_data.to_dict()

            # Generate new story response if needed
            if not story_exists or not bias_exists:
                logger.info(f"Generating new Anthropic response for {hero_name} in {story_name}")
                prompt_path = await self.prompt_manager.generate_and_save_prompt(
                    story_data,
                    hero_name
                )

                with open(prompt_path, 'r') as f:
                    prompt = f.read()

                # Generate story using Anthropic
                request = {"content": prompt}
                response = await self.anthropic_processor._process_single_request(request)
                if not isinstance(response, APIResponse):
                    raise ValueError("Invalid response type from Anthropic processor")

                # Process and save response
                response_path = await self.anthropic_handler.process_and_save_response(
                    response=response,
                    story_name=formatted_name,
                    hero_name=hero_name,
                    model=ANTHROPIC_MODEL
                )

                # Load saved response
                response_data = await self.anthropic_handler.load_response(response_path)
            else:
                # Load existing response if we only need to generate bias report
                formatted_hero = self.story_manager.format_story_name({"story": {"title": hero_name}})
                response_path = Path(self.output_dir) / formatted_name / 'anthropic' / f"response_{formatted_hero}.json"
                response_data = await self.anthropic_handler.load_response(response_path)

            # Generate bias report if needed
            if not bias_exists or not story_exists:
                logger.info(f"Generating bias report for {hero_name} in {story_name}")
                story_id = os.path.splitext(story_name)[0]  # Remove .json extension
                await self.bias_report_generator.generate_bias_report(story_id)
            
            return response_data.to_dict()

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
            story_path = Path(self.story_manager.story_dir) / story_name
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
            story_path = Path(self.story_manager.story_dir) / story_name
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
                        # Convert responses to dicts if needed
                        response_dicts = [
                            r if isinstance(r, dict) else r.to_dict()
                            for r in responses
                        ]
                        # Count existing vs new responses
                        existing_count = sum(1 for r in response_dicts if r.get('metadata', {}).get('existing', False))
                        logger.debug(f"Found {existing_count} existing responses for {provider}")
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
