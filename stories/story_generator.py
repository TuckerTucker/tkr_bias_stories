# stories/story_generator.py

import json
import os
import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime
from tkr_utils.config_logging import setup_logging
from tkr_utils.decorators import logs_and_exceptions
from tkr_utils.helper_openai import OpenAIHelper
from tkr_utils.helper_anthropic.client import AnthropicHelper
from tkr_utils.helper_anthropic.models import RateLimits, APIResponse
from tkr_utils.helper_anthropic.processor import RequestProcessor
from tkr_utils.app_paths import AppPaths
from stories.story_manager import StoryManager
from stories.models import StoryResponse
from prompts.prompt_manager import PromptManager
from stories.response_handlers import AnthropicResponseHandler, OpenAIResponseHandler
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

    ###################
    # OpenAI Methods #
    ###################

    @logs_and_exceptions(logger)
    async def save_response_openai(
        self,
        response: Dict[str, Any],
        story_name: str,
        hero_name: str
    ) -> str:
        """Save OpenAI LLM response using standardized format.

        Args:
            response: OpenAI completion response from helper
            story_name: Name of the story
            hero_name: Name of the hero character

        Returns:
            str: Path where response was saved
        """
        try:
            # Create provider-specific directory
            story_dir = os.path.join(self.output_dir, story_name, 'openai')
            os.makedirs(story_dir, exist_ok=True)

            # Get response content and usage from OpenAI response
            content = response.choices[0].message.content
            usage = response.usage.model_dump()

            # Create standardized response
            standardized_response = StoryResponse(
                story_id=story_name,
                hero=hero_name,
                text=content,
                metadata={
                    'provider': 'openai',
                    'model': self.llm_openai.model,
                    'total_tokens': usage['total_tokens'],
                    'generated_at': datetime.now().isoformat(),
                    'usage': {
                        'input_tokens': usage['prompt_tokens'],
                        'output_tokens': usage['completion_tokens'],
                        'total_tokens': usage['total_tokens']
                    }
                }
            )

            # Create filename from hero name
            hero_filename = f"response_{hero_name.lower().replace(' ', '_')}.json"
            response_path = os.path.join(story_dir, hero_filename)

            # Save standardized response
            with open(response_path, 'w') as f:
                json.dump(standardized_response.to_dict(), f, indent=2)

            logger.info(f"Successfully saved OpenAI response to {response_path}")
            return response_path

        except Exception as e:
            logger.error(f"Error saving OpenAI response: {str(e)}")
            raise

    @logs_and_exceptions(logger)
    async def generate_single_story_openai(
        self,
        story_name: str,
        hero_name: str
    ) -> Dict[str, Any]:
        """Generate a single story variation with OpenAI."""
        try:
            # Load story data and generate prompt (unchanged)
            story_path = f"{self.story_manager.story_dir}/{story_name}"
            story_data = await self.story_manager.load_story(story_path)
            prompt_path = await self.prompt_manager.generate_and_save_prompt(
                story_data,
                hero_name
            )

            with open(prompt_path, 'r') as f:
                prompt = f.read()

            # Prepare and send messages
            messages = [{"role": "user", "content": prompt}]
            response = await self.llm_openai.send_message_json_async(messages=messages)

            # Use new handler to process and save response
            formatted_name = self.story_manager.format_story_name(story_data)
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
            logger.error(f"Error generating OpenAI story: {str(e)}")
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

    #####################
    # Anthropic Methods #
    #####################

    @logs_and_exceptions(logger)
    async def save_response_anthropic(
        self,
        response: APIResponse,
        story_name: str,
        hero_name: str
    ) -> str:
        """Save Anthropic LLM response using standardized format.

        Args:
            response: APIResponse from Anthropic
            story_name: Name of the story
            hero_name: Name of the hero character

        Returns:
            str: Path where response was saved
        """
        try:
            # Create provider-specific directory
            story_dir = os.path.join(self.output_dir, story_name, 'anthropic')
            os.makedirs(story_dir, exist_ok=True)

            # Parse response content
            content = json.loads(response.content) if response.success else {"text": ""}

            # Create standardized response
            standardized_response = StoryResponse(
                story_id=story_name,
                hero=hero_name,
                text=content.get('text', ''),
                metadata={
                    'provider': 'anthropic',
                    'model': self.anthropic_client.model,
                    'total_tokens': response.metadata.get('usage', {}).get('total_tokens', 0) if response.metadata else 0,
                    'generated_at': datetime.now().isoformat()
                }
            )

            # Save response
            hero_filename = f"response_{hero_name.lower().replace(' ', '_')}.json"
            response_path = os.path.join(story_dir, hero_filename)

            with open(response_path, 'w') as f:
                json.dump(standardized_response.to_dict(), f, indent=2)

            logger.info(f"Successfully saved Anthropic response to {response_path}")
            return response_path

        except Exception as e:
            logger.error(f"Error saving Anthropic response: {str(e)}")
            raise

    @logs_and_exceptions(logger)
    async def generate_single_story_anthropic(
        self,
        story_name: str,
        hero_name: str
    ) -> Dict[str, Any]:
        """Generate a single story variation with Anthropic."""
        try:
            # Load story data and generate prompt (unchanged)
            story_path = f"{self.story_manager.story_dir}/{story_name}"
            story_data = await self.story_manager.load_story(story_path)
            prompt_path = await self.prompt_manager.generate_and_save_prompt(
                story_data,
                hero_name
            )

            with open(prompt_path, 'r') as f:
                prompt = f.read()

            # Create request for processor
            request = {"content": prompt}
            response = await self.anthropic_processor._process_single_request(request)

            # Use new handler to process and save response
            formatted_name = self.story_manager.format_story_name(story_data)
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
            logger.error(f"Error generating Anthropic story: {str(e)}")
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

    ################
    # Main Methods #
    ################

    async def list_available_stories(self) -> List[Dict[str, str]]:
        """Get list of all available stories."""
        try:
            stories = self.story_manager.get_all_stories()
            logger.info(f"Found {len(stories)} available stories")
            return stories
        except Exception as e:
            logger.error(f"Error listing stories: {str(e)}")
            raise

async def main():
    """Main entry point for the application."""

    story_name = "traffic_stop_food.json"

    try:
        app = StoryGenerationApp()

        # List available stories
        stories = await app.list_available_stories()
        logger.info("Available stories:")
        for story in stories:
            logger.info(f"- {story['title']}")

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

        # Process responses
        all_responses = {
            "openai": openai_responses if not isinstance(openai_responses, Exception) else [],
            "anthropic": anthropic_responses if not isinstance(anthropic_responses, Exception) else []
        }

        # Log completion status
        total_stories = len(all_responses["openai"]) + len(all_responses["anthropic"])
        logger.info(f"Story generation completed. Total stories generated: {total_stories}")

        return all_responses

    except Exception as e:
        logger.error(f"Application error: {str(e)}")
        raise

if __name__ == "__main__":
    asyncio.run(main())
