# app.py

import json
import os
import asyncio
from typing import List, Dict, Any, Optional
from tkr_utils.config_logging import setup_logging
from tkr_utils.decorators import logs_and_exceptions
from tkr_utils.helper_openai import OpenAIHelper
from tkr_utils.helper_anthropic.client import AnthropicBatchClient
from tkr_utils.helper_anthropic.models import RateLimits
from tkr_utils.helper_anthropic.processor import RequestProcessor
from tkr_utils.app_paths import AppPaths
from stories.story_manager import StoryManager
from prompts.prompt_manager import PromptManager
from tkr_utils.config import (
    ANTHROPIC_API_KEY,
    ANTHROPIC_MODEL,
    MAX_REQUESTS_PER_MINUTE,
    MAX_TOKENS_PER_MINUTE
)

logger = setup_logging(__file__)

class StoryGenerationApp:
    """Main application orchestrator for story generation."""

    def __init__(self) -> None:
        """Initialize application components."""
        self.story_manager = StoryManager()
        self.prompt_manager = PromptManager()
        self.llm_openai = OpenAIHelper(async_mode=True)

        """Initialize application components."""
        if not ANTHROPIC_API_KEY:
            raise ValueError("ANTHROPIC_API_KEY environment variable is required")

        # Initialize rate limits with integer values
        rate_limits = RateLimits(
            requests_per_minute=int(MAX_REQUESTS_PER_MINUTE),
            tokens_per_minute=int(MAX_TOKENS_PER_MINUTE)
        )

        self.anthropic_client = AnthropicBatchClient(
            api_key=ANTHROPIC_API_KEY,
            model=ANTHROPIC_MODEL
        )
        self.anthropic_processor = RequestProcessor(
            client=self.anthropic_client,
            rate_limits=rate_limits
        )

        self.output_dir = AppPaths.LOCAL_DATA
        logger.info("Initialized StoryGenerationApp with OpenAI and Anthropic batch processing")

    @logs_and_exceptions(logger)
    async def save_response_openai(
        self,
        response: Dict[str, Any],
        story_name: str,
        hero_name: str
    ) -> str:
        """
        Save OpenAI LLM response to local directory.

        Args:
            response (Dict[str, Any]): LLM response to save
            story_name (str): Name of the story
            hero_name (str): Name of the hero character

        Returns:
            str: Path where response was saved

        Raises:
            OSError: If directory creation or file writing fails
        """
        try:
            # Create provider-specific directory
            story_dir = os.path.join(self.output_dir, story_name, 'openai')
            os.makedirs(story_dir, exist_ok=True)

            # Create filename from hero name
            hero_filename = f"response_{hero_name.lower().replace(' ', '_')}.json"
            response_path = os.path.join(story_dir, hero_filename)

            # Save response to file
            with open(response_path, 'w') as f:
                json.dump(response, f, indent=2)

            logger.info(f"Successfully saved OpenAI response to {response_path}")
            return response_path

        except Exception as e:
            logger.error(f"Error saving OpenAI response: {str(e)}")
            raise

    @logs_and_exceptions(logger)
    async def save_response_anthropic(
        self,
        response: Dict[str, Any],
        story_name: str,
        hero_name: str
    ) -> str:
        """
        Save Anthropic LLM response to local directory.

        Args:
            response (Dict[str, Any]): LLM response to save
            story_name (str): Name of the story
            hero_name (str): Name of the hero character

        Returns:
            str: Path where response was saved
        """
        try:
            # Create provider-specific directory
            story_dir = os.path.join(self.output_dir, story_name, 'anthropic')
            os.makedirs(story_dir, exist_ok=True)

            # Create filename from hero name
            hero_filename = f"response_{hero_name.lower().replace(' ', '_')}.json"
            response_path = os.path.join(story_dir, hero_filename)

            # Save response to file
            with open(response_path, 'w') as f:
                json.dump(response, f, indent=2)

            logger.info(f"Successfully saved Anthropic response to {response_path}")
            return response_path

        except Exception as e:
            logger.error(f"Error saving Anthropic response: {str(e)}")
            raise

    @logs_and_exceptions(logger)
    async def generate_single_story_openai(
        self,
        story_name: str,
        hero_name: str
    ) -> Dict[str, Any]:
        """Generate a single story variation with OpenAI."""
        try:
            # Load story data
            story_path = f"{self.story_manager.story_dir}/{story_name}"
            story_data = await self.story_manager.load_story(story_path)

            # Generate and save prompt
            prompt_path = await self.prompt_manager.generate_and_save_prompt(
                story_data,
                hero_name
            )

            # Read generated prompt
            with open(prompt_path, 'r') as f:
                prompt = f.read()

            # Send to OpenAI
            messages = [{"role": "user", "content": prompt}]
            response = await self.llm_openai.send_message_json_async(messages)

            # Extract the content and add LLM metadata
            response_data = {
                "story": {
                    "title": story_data['story']['title'],
                    "hero": hero_name,
                    "llm": {
                        "provider": "OpenAI",
                        "model": self.llm_openai.model
                    },
                    "response": json.loads(response.choices[0].message.content)
                }
            }

            # Save response
            formatted_name = self.story_manager.format_story_name(story_data)
            await self.save_response_openai(response_data, formatted_name, hero_name)

            logger.info(f"Successfully generated OpenAI story for {hero_name} in {story_name}")
            return response_data

        except Exception as e:
            logger.error(f"Error generating OpenAI story: {str(e)}")
            raise

    @logs_and_exceptions(logger)
    async def generate_single_story_anthropic(
        self,
        story_name: str,
        hero_name: str
    ) -> Dict[str, Any]:
        """Generate a single story variation with Anthropic batch processing."""
        try:
            # Load story data
            story_path = f"{self.story_manager.story_dir}/{story_name}"
            story_data = await self.story_manager.load_story(story_path)

            # Generate and save prompt
            prompt_path = await self.prompt_manager.generate_and_save_prompt(
                story_data,
                hero_name
            )

            # Read generated prompt
            with open(prompt_path, 'r') as f:
                prompt = f.read()

            # Prepare request for batch processing - single message dictionary
            message = {"role": "user", "content": prompt}

            # Process single request through batch processor
            responses = await self.anthropic_processor.process_batch(
                messages=[message],  # Pass list of message dictionaries
                output_file=None
            )

            # Extract the first (and only) response
            response_content = responses[0] if responses else "{}"

            # Extract the content and add LLM metadata
            response_data = {
                "story": {
                    "title": story_data['story']['title'],
                    "hero": hero_name,
                    "llm": {
                        "provider": "Anthropic",
                        "model": self.anthropic_client.helper.model
                    },
                    "response": json.loads(response_content)
                }
            }

            # Save response
            formatted_name = self.story_manager.format_story_name(story_data)
            await self.save_response_anthropic(response_data, formatted_name, hero_name)

            logger.info(f"Successfully generated Anthropic story for {hero_name} in {story_name}")
            return response_data

        except Exception as e:
            logger.error(f"Error generating Anthropic story: {str(e)}")
            raise

    @logs_and_exceptions(logger)
    async def generate_all_variations_openai(
        self,
        story_name: str
    ) -> List[Dict[str, Any]]:
        """
        Generate stories for all hero variants using OpenAI.

        Args:
            story_name (str): Name of the story file

        Returns:
            List[Dict[str, Any]]: List of generated story responses
        """
        try:
            story_path = f"{self.story_manager.story_dir}/{story_name}"
            story_data = await self.story_manager.load_story(story_path)

            tasks = []
            for hero in story_data['story']['hero']:
                task = self.generate_single_story_openai(story_name, hero)
                tasks.append(task)

            responses = await asyncio.gather(*tasks)
            logger.info(f"Successfully generated all OpenAI variations for {story_name}")
            return responses

        except Exception as e:
            logger.error(f"Error generating OpenAI story variations: {str(e)}")
            raise

    @logs_and_exceptions(logger)
    async def generate_all_variations_anthropic(
        self,
        story_name: str
    ) -> List[Dict[str, Any]]:
        """Generate stories for all hero variants using Anthropic batch processing."""
        try:
            story_path = f"{self.story_manager.story_dir}/{story_name}"
            story_data = await self.story_manager.load_story(story_path)

            # Prepare all requests
            messages = []
            for hero in story_data['story']['hero']:
                prompt_path = await self.prompt_manager.generate_and_save_prompt(
                    story_data,
                    hero
                )
                with open(prompt_path, 'r') as f:
                    prompt = f.read()
                messages.append({"role": "user", "content": prompt})

            # Process all requests in batch
            batch_responses = await self.anthropic_processor.process_batch(
                messages=messages,
                output_file=None
            )

            # Format and save responses
            formatted_responses = []
            formatted_name = self.story_manager.format_story_name(story_data)

            for hero, response in zip(story_data['story']['hero'], batch_responses):
                response_data = {
                    "story": {
                        "title": story_data['story']['title'],
                        "hero": hero,
                        "llm": {
                            "provider": "Anthropic",
                            "model": self.anthropic_client.helper.model
                        },
                        "response": json.loads(response)
                    }
                }

                # Save individual response
                await self.save_response_anthropic(
                    response_data,
                    formatted_name,
                    hero
                )
                formatted_responses.append(response_data)

            logger.info(f"Successfully generated all Anthropic variations for {story_name}")
            return formatted_responses

        except Exception as e:
            logger.error(f"Error generating Anthropic story variations: {str(e)}")
            raise

    @logs_and_exceptions(logger)
    async def list_available_stories(self) -> List[Dict[str, str]]:
        """
        Get list of all available stories.

        Returns:
            List[Dict[str, str]]: List of story titles and paths
        """
        try:
            stories = self.story_manager.get_all_stories()
            logger.info(f"Found {len(stories)} available stories")
            return stories
        except Exception as e:
            logger.error(f"Error listing stories: {str(e)}")
            raise

async def main():
    """Main entry point for the application."""

    the_story = "traffic_stop_food.json"

    try:
        app = StoryGenerationApp()

        # List available stories
        stories = await app.list_available_stories()
        logger.info("Available stories:")
        for story in stories:
            logger.info(f"- {story['title']}")

        story_name = the_story

        # Create tasks for both providers
        openai_task = app.generate_all_variations_openai(story_name)
        anthropic_task = app.generate_all_variations_anthropic(story_name)

        # Run both tasks concurrently
        results = await asyncio.gather(
            openai_task,
            anthropic_task,
            return_exceptions=True
        )

        openai_responses, anthropic_responses = results

        # Process OpenAI responses
        if isinstance(openai_responses, Exception):
            logger.error(f"OpenAI generation failed: {str(openai_responses)}")
            openai_responses = []
        elif isinstance(openai_responses, list):
            logger.info(f"Generated {len(openai_responses)} OpenAI story variations")

        # Process Anthropic responses
        if isinstance(anthropic_responses, Exception):
            logger.error(f"Anthropic generation failed: {str(anthropic_responses)}")
            anthropic_responses = []
        elif isinstance(anthropic_responses, list):
            logger.info(f"Generated {len(anthropic_responses)} Anthropic story variations")

        # Combine responses
        all_responses = {
            "openai": openai_responses,
            "anthropic": anthropic_responses
        }

        # Log completion status
        total_stories = (len(openai_responses) if isinstance(openai_responses, list) else 0) + \
                       (len(anthropic_responses) if isinstance(anthropic_responses, list) else 0)
        logger.info(f"Story generation completed. Total stories generated: {total_stories}")

        return all_responses

    except Exception as e:
        logger.error(f"Application error: {str(e)}")
        raise

if __name__ == "__main__":
    asyncio.run(main())
