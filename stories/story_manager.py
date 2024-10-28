# stories/story_manager.py

import json
import os
from typing import List, Dict, Any
from pathlib import Path
from tkr_utils.config_logging import setup_logging
from tkr_utils.decorators import logs_and_exceptions
from tkr_utils.app_paths import AppPaths

logger = setup_logging(__file__)

class StoryManager:
    """Manages story loading and processing operations."""

    def __init__(self) -> None:
        """Initialize StoryManager with story directory path."""
        self.story_dir = os.path.join(AppPaths.BASE_DIR, 'stories', 'outlines')
        logger.info(f"Initialized StoryManager with story directory: {self.story_dir}")

    @staticmethod
    def format_story_name(story_data: Dict[str, Any]) -> str:
        """
        Format story name consistently for directory/file naming using story title.

        Args:
            story_data (Dict[str, Any]): Story data dictionary containing title

        Returns:
            str: Formatted story name
        """
        title = story_data['story']['title']
        return title.lower().replace(' ', '_')

    @logs_and_exceptions(logger)
    def get_all_stories(self) -> List[Dict[str, Any]]:
        """
        Get all available stories with proper ID and path handling.

        Returns:
            List[Dict[str, Any]]: List of story data including IDs
        """
        stories = []
        try:
            for filename in os.listdir(self.story_dir):
                if filename.endswith('.json'):
                    file_path = os.path.join(self.story_dir, filename)
                    with open(file_path, 'r') as f:
                        story_data = json.load(f)
                        # Create story ID from filename without extension
                        story_id = os.path.splitext(filename)[0]

                        stories.append({
                            'id': story_id,
                            'path': file_path,
                            **story_data['story']
                        })

                        logger.debug(f"Loaded story {story_id} from {file_path}")

            logger.info(f"Successfully loaded {len(stories)} stories")
            return stories

        except Exception as e:
            logger.error(f"Error reading stories: {str(e)}")
            return []

    @logs_and_exceptions(logger)
    async def load_story(self, story_path: str) -> Dict[str, Any]:
        """
        Loads a specific story from its JSON file.

        Args:
            story_path (str): Path to the story JSON file.

        Returns:
            Dict[str, Any]: Story data dictionary.

        Raises:
            FileNotFoundError: If story file doesn't exist.
            json.JSONDecodeError: If story file is invalid JSON.
        """
        try:
            with open(story_path, 'r') as f:
                story_data = json.load(f)

            if self.validate_story_format(story_data):
                logger.info(f"Successfully loaded story from {story_path}")
                return story_data
            else:
                raise ValueError("Invalid story format")

        except FileNotFoundError:
            logger.error(f"Story file not found: {story_path}")
            raise
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in story file: {story_path}")
            raise
        except Exception as e:
            logger.error(f"Error loading story: {str(e)}")
            raise

    @staticmethod
    def validate_story_format(story_data: Dict[str, Any]) -> bool:
        """
        Validates that story data matches expected format.

        Args:
            story_data (Dict[str, Any]): Story data to validate.

        Returns:
            bool: True if valid, False otherwise.
        """
        try:
            # Check required fields exist
            assert 'story' in story_data
            assert 'title' in story_data['story']
            assert 'plot' in story_data['story']
            assert 'hero' in story_data['story']

            # Validate hero is a list
            assert isinstance(story_data['story']['hero'], list)

            # Validate title and plot are strings
            assert isinstance(story_data['story']['title'], str)
            assert isinstance(story_data['story']['plot'], str)

            return True

        except AssertionError:
            logger.error("Story validation failed")
            return False
