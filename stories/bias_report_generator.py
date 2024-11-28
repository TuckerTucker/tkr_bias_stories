#!/usr/bin/env python3
"""
Bias Report Generator Module

This module generates bias reports for stories using Anthropic's analysis.
"""

import json
import os
from pathlib import Path
from typing import Dict, Any, Optional
import asyncio
from datetime import datetime

from tkr_utils.config_logging import setup_logging
from tkr_utils.decorators import logs_and_exceptions
from tkr_utils.helper_anthropic.client import AnthropicHelper
from tkr_utils.app_paths import AppPaths
from tkr_utils.config import (
    ANTHROPIC_API_KEY,
    ANTHROPIC_MODEL
)

from stories.story_manager import StoryManager
from prompts.prompt_manager import PromptManager
from stories.models import FileExistenceStatus

logger = setup_logging(__file__)

class BiasReportGenerator:
    """Generates bias reports for stories using Anthropic's analysis."""

    def __init__(
        self,
        story_manager: StoryManager,
        prompt_manager: PromptManager
    ) -> None:
        """Initialize the BiasReportGenerator.

        Args:
            story_manager: StoryManager instance for handling story data
            prompt_manager: PromptManager instance for handling prompts
        """
        self.story_manager = story_manager
        self.prompt_manager = prompt_manager
        
        # Initialize Anthropic components
        if not ANTHROPIC_API_KEY:
            raise ValueError("ANTHROPIC_API_KEY environment variable is required")

        self.anthropic_client = AnthropicHelper(
            api_key=ANTHROPIC_API_KEY,
            model=ANTHROPIC_MODEL
        )

        # Set up output directory
        self.output_dir = Path(AppPaths.LOCAL_DATA)

        logger.info("Initialized BiasReportGenerator")

    def _format_filename(self, hero: str) -> str:
        """Format hero name for consistent filename usage."""
        # Use StoryManager's format_story_name for consistency
        return self.story_manager.format_story_name({"story": {"title": hero}})

    async def _get_story_content(self, story_dir: Path, provider: str, hero: str) -> Optional[str]:
        """Get story content for a specific hero."""
        try:
            # Build response file path
            response_file = story_dir / provider / f"response_{self._format_filename(hero)}.json"
            logger.debug(f"Looking for story content in: {response_file}")
            
            if not response_file.exists():
                logger.warning(f"Response file not found: {response_file}")
                return None

            with open(response_file, 'r') as f:
                data = json.load(f)
                logger.debug(f"Loaded response data: {data}")
                
                # Try to extract text from different possible locations
                if isinstance(data, dict):
                    if 'text' in data:
                        return data['text']
                    elif f'{hero.lower()}_story' in data and 'text' in data[f'{hero.lower()}_story']:
                        return data[f'{hero.lower()}_story']['text']
                
                logger.warning(f"Could not find text content in response data for {hero}")
                return None
                
        except Exception as e:
            logger.error(f"Error reading story content: {e}")
            return None

    async def _save_bias_report(self, story_dir: Path, provider: str, hero: str, report: Dict[str, Any]) -> None:
        """Save the bias report for a specific hero."""
        try:
            # Ensure provider directory exists
            provider_dir = story_dir / provider
            provider_dir.mkdir(parents=True, exist_ok=True)
            logger.debug(f"Ensuring provider directory exists: {provider_dir}")

            # Create report file path
            report_file = provider_dir / f"bias_report_{self._format_filename(hero)}.json"
            logger.debug(f"Saving bias report to: {report_file}")

            with open(report_file, 'w') as f:
                json.dump(report, f, indent=2)
            logger.info(f"Successfully saved bias report: {report_file}")
            
        except Exception as e:
            logger.error(f"Error saving bias report: {str(e)}")
            logger.error(f"Report data that failed to save: {report}")
            raise

    @logs_and_exceptions(logger)
    async def _check_files_exist(
        self,
        story_dir: Path,
        provider: str,
        hero: str
    ) -> FileExistenceStatus:
        """Check existence of story response and bias report files atomically.
        
        Args:
            story_dir: Directory containing the files
            provider: Provider name (openai/anthropic)
            hero: Hero name
            
        Returns:
            FileExistenceStatus containing existence flags and metadata
        """
        try:
            formatted_hero = self.story_manager.format_story_name(
                {"story": {"title": hero}}
            )
            
            # Get paths
            provider_dir = story_dir / provider
            story_path = provider_dir / f"response_{formatted_hero}.json"
            bias_path = provider_dir / f"bias_report_{formatted_hero}.json"
            
            # Check both files at same time point
            check_time = datetime.now()
            story_exists = story_path.exists()
            bias_exists = bias_path.exists()
            
            status = FileExistenceStatus(
                story_exists=story_exists,
                bias_exists=bias_exists,
                checked_at=check_time,
                story_path=story_path,
                bias_path=bias_path
            )
            
            logger.info(
                f"File check at {check_time.isoformat()}: "
                f"story={story_exists}, bias={bias_exists} "
                f"for {provider}/{formatted_hero}"
            )
            
            return status
            
        except Exception as e:
            logger.error(f"Error checking file existence: {str(e)}")
            raise

    @logs_and_exceptions(logger)
    async def generate_bias_report(self, story_name: Optional[str] = None) -> None:
        """
        Generate bias reports for stories based on existing response files.
        
        Args:
            story_name: Optional specific story to process. If None, processes all stories.
        """
        try:
            # Load templates
            bias_prompt = await self.prompt_manager.load_template('bias_prompt.md')
            bias_template = await self.prompt_manager.load_template('templates/bias.template')

            # Process all stories if none specified
            if story_name:
                # Load specific story
                story_path = Path(self.story_manager.story_dir) / f"{story_name}.json"
                story_data = await self.story_manager.load_story(story_path)
                stories = [story_data] if story_data else []
            else:
                # Load all stories
                stories = []
                for story_file in Path(self.story_manager.story_dir).glob('*.json'):
                    story_data = await self.story_manager.load_story(story_file)
                    if story_data:
                        stories.append(story_data)

            # Create tasks for all stories
            tasks = []
            for story_data in stories:
                story_title = story_data['story']['title']
                formatted_name = self.story_manager.format_story_name({"story": {"title": story_title}})
                story_dir = self.output_dir / formatted_name

                # Create tasks for each provider and hero
                for provider in ['openai', 'anthropic']:
                    for hero in story_data['story']['hero']:
                        task = self._process_single_bias_report(
                            story_data=story_data,
                            story_dir=story_dir,
                            provider=provider,
                            hero=hero,
                            bias_prompt=bias_prompt,
                            bias_template=bias_template
                        )
                        tasks.append(task)

            # Process all tasks concurrently
            if tasks:
                results = await asyncio.gather(*tasks, return_exceptions=True)
                
                # Log results
                success_count = sum(1 for r in results if r is True)
                error_count = sum(1 for r in results if isinstance(r, Exception))
                logger.info(f"Completed bias report generation. Successes: {success_count}, Errors: {error_count}")

        except Exception as e:
            logger.error(f"Error in generate_bias_report: {str(e)}")
            raise

    @logs_and_exceptions(logger)
    async def _process_single_bias_report(
        self,
        story_data: Dict[str, Any],
        story_dir: Path,
        provider: str,
        hero: str,
        bias_prompt: Any,
        bias_template: Any
    ) -> bool:
        """Process a single bias report for a specific hero.

        Args:
            story_data: Story data dictionary
            story_dir: Path to story directory
            provider: Provider name (openai/anthropic)
            hero: Hero name
            bias_prompt: Loaded bias prompt template
            bias_template: Loaded bias template

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            story_title = story_data['story']['title']
            formatted_name = self.story_manager.format_story_name({"story": {"title": story_title}})
            
            # Check files atomically
            status = await self._check_files_exist(story_dir, provider, hero)
            
            # Only process if we have both files or need to regenerate bias report
            if not status.should_process:
                logger.info(f"Skipping {story_title}/{provider}/{hero} - already processed")
                return True
                
            # Get story content from existing file only
            content = await self._get_story_content(story_dir, provider, hero)
            if not content:
                logger.warning(f"No existing story content found for {story_title}/{provider}/{hero}")
                return False

            if not content:
                logger.error(f"No content available for {story_title}/{provider}/{hero}")
                return False

            # Generate bias report if needed
            if not status.bias_exists or not status.story_exists:
                try:
                    # First render the analysis prompt with the story content
                    analysis_instructions = bias_prompt.render(
                        story=content
                    )

                    # Then create the complete prompt with the template structure
                    complete_prompt = f"""
{analysis_instructions}

Please analyze the following story for bias and provide your analysis in this exact JSON format:

{bias_template.render()}

Story to analyze:
{content}
"""
                    # Get bias analysis from Anthropic
                    response = await self.anthropic_client.send_message(
                        messages=[{
                            "role": "user",
                            "content": complete_prompt
                        }]
                    )

                    # Parse the response as JSON to validate it
                    try:
                        bias_report = json.loads(response.content)
                    except json.JSONDecodeError:
                        logger.error(f"Invalid JSON response for {story_title}/{provider}/{hero}")
                        return False

                    # Save bias report
                    await self._save_bias_report(
                        story_dir=story_dir,
                        provider=provider,
                        hero=hero,
                        report=bias_report
                    )
                    
                    return True

                except Exception as e:
                    logger.error(f"Error generating bias report: {str(e)}")
                    return False

            return True

        except Exception as e:
            logger.error(f"Error processing bias report for {story_title}/{provider}/{hero}: {str(e)}")
            return False

async def main(story_name: Optional[str] = None):
    """Main entry point for bias report generation."""
    story_manager = StoryManager()
    prompt_manager = PromptManager()
    from story_generation_app import StoryGenerationApp
    story_gen_app = StoryGenerationApp()
    generator = BiasReportGenerator(
        story_manager,
        prompt_manager
    )
    await generator.generate_bias_report(story_name)

if __name__ == "__main__":
    import sys
    story_name = sys.argv[1] if len(sys.argv) > 1 else None
    asyncio.run(main(story_name))
