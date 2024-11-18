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
        self.prompts_dir = os.path.join(AppPaths.BASE_DIR, 'prompts')
        self.templates_dir = os.path.join(self.prompts_dir, 'templates')
        self.output_dir = AppPaths.LOCAL_DATA

        # Setup Jinja2 environment
        self.env = Environment(
            loader=FileSystemLoader([self.prompts_dir, self.templates_dir]),
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
            story_dir = os.path.join(self.output_dir, story_name)
            os.makedirs(story_dir, exist_ok=True)

            # Save prompt to file
            prompt_path = os.path.join(story_dir, f'{story_name}_prompt.md')
            with open(prompt_path, 'w') as f:
                f.write(prompt)

            logger.info(f"Successfully saved prompt to {prompt_path}")
            return prompt_path

        except OSError as e:
            logger.error(f"Error saving prompt: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error saving prompt: {str(e)}")
            raise

    @logs_and_exceptions(logger)
    async def generate_and_save_prompt(self, story_data: Dict[str, Any], hero_name: str) -> str:
        """Convenience method to generate and save a prompt in one step."""
        try:
            # Generate the prompt
            prompt = await self.create_prompt(story_data, hero_name)

            # Use StoryManager formatted name from title
            story_name = StoryManager.format_story_name(story_data)
            saved_path = await self.save_prompt(prompt, story_name)

            logger.info(f"Successfully generated and saved prompt for {story_name}")
            return saved_path

        except Exception as e:
            logger.error(f"Error in generate_and_save_prompt: {str(e)}")
            raise
