# prompts/prompt_manager.py

import os
from pathlib import Path
from typing import Dict, Any
from jinja2 import Environment, FileSystemLoader, select_autoescape
from tkr_utils.config_logging import setup_logging
from tkr_utils.decorators import logs_and_exceptions
from tkr_utils.app_paths import AppPaths
from stories.story_manager import StoryManager

logger = setup_logging(__file__)

class PromptManager:
    """Manages prompt creation and storage operations using Jinja2 templating."""

    def __init__(self) -> None:
        """Initialize PromptManager with template paths and Jinja2 environment."""
        self.prompts_dir = Path(AppPaths.BASE_DIR) / 'prompts'
        self.templates_dir = self.prompts_dir / 'templates'
        self.output_dir = Path(AppPaths.LOCAL_DATA)

        # Setup Jinja2 environment
        self.env = Environment(
            loader=FileSystemLoader([str(self.prompts_dir), str(self.templates_dir)]),
            autoescape=select_autoescape(['html', 'xml']),
            trim_blocks=True,
            lstrip_blocks=True
        )

        logger.info(f"Initialized PromptManager with prompts directory: {self.prompts_dir}")

    @logs_and_exceptions(logger)
    async def load_template(self, template_name: str) -> Any:
        """
        Loads a Jinja2 template by name.

        Args:
            template_name (str): Name of the template file.

        Returns:
            Any: Jinja2 Template object.

        Raises:
            TemplateNotFound: If template file doesn't exist.
        """
        try:
            template = self.env.get_template(template_name)
            logger.info(f"Successfully loaded template: {template_name}")
            return template
        except Exception as e:
            logger.error(f"Error loading template {template_name}: {str(e)}")
            raise

    @logs_and_exceptions(logger)
    async def create_prompt(self, story_data: Dict[str, Any], hero_name: str) -> str:
        """
        Generates a story prompt using Jinja2 template.

        Args:
            story_data (Dict[str, Any]): Story data dictionary.
            hero_name (str): Name of the hero character.

        Returns:
            str: Generated prompt.
        """
        try:
            # Load story prompt template
            story_prompt = await self.load_template('story_prompt.md')

            # Create context for story template
            story_context = {
                'title': story_data['story']['title'],
                'plot': story_data['story']['plot'].replace('{{ hero }}', hero_name)
            }

            # Render story template
            prompt = story_prompt.render(**story_context)

            logger.info(f"Successfully created prompt for story '{story_data['story']['title']}' with hero '{hero_name}'")
            return prompt

        except Exception as e:
            logger.error(f"Error creating prompt: {str(e)}")
            raise

    @logs_and_exceptions(logger)
    async def save_prompt(self, prompt: str, story_name: str) -> str:
        """
        Saves generated prompt to local directory.

        Args:
            prompt (str): Generated prompt content.
            story_name (str): Name of the story (used for directory name).

        Returns:
            str: Path where prompt was saved.

        Raises:
            OSError: If directory creation or file writing fails.
        """
        try:
            # Create story directory if it doesn't exist
            story_dir = self.output_dir / story_name
            story_dir.mkdir(parents=True, exist_ok=True)

            # Save prompt to file
            prompt_path = story_dir / f'{story_name}_prompt.md'
            prompt_path.write_text(prompt, encoding='utf-8')

            logger.info(f"Successfully saved prompt to {prompt_path}")
            return str(prompt_path)

        except OSError as e:
            logger.error(f"Error saving prompt: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error saving prompt: {str(e)}")
            raise

    @logs_and_exceptions(logger)
    async def generate_and_save_prompt(self, story_data: Dict[str, Any], hero_name: str) -> Path:
        """
        Generate and save a prompt for a specific story and hero.

        Args:
            story_data (Dict[str, Any]): Story data dictionary
            hero_name (str): Name of the hero character

        Returns:
            Path: Path to the saved prompt file
        """
        try:
            # Get formatted story name
            story_title = story_data['story']['title']
            formatted_name = StoryManager.format_story_name({"story": {"title": story_title}})
            formatted_hero = StoryManager.format_story_name({"story": {"title": hero_name}})

            # Create output directory if it doesn't exist
            output_dir = self.output_dir / formatted_name / 'prompts'
            output_dir.mkdir(parents=True, exist_ok=True)

            # Generate prompt using template
            template = await self.load_template('story_prompt.md')
            prompt = template.render(
                plot=story_data['story']['plot'].replace('{{ hero }}', hero_name)
            )

            # Save prompt to file
            output_path = output_dir / f"prompt_{formatted_hero}.md"
            output_path.write_text(prompt, encoding='utf-8')

            logger.info(f"Successfully saved prompt to {output_path}")
            return output_path

        except Exception as e:
            logger.error(f"Error generating prompt for {hero_name}: {str(e)}")
            raise
