#!/usr/bin/env python3
"""
Story Manager Module

This module provides functionality for managing story loading and processing operations,
handling both story outlines and generated responses.
"""

import json
import os
import re
from pathlib import Path
from typing import List, Dict, Any, Optional

from tkr_utils.config_logging import setup_logging
from tkr_utils.decorators import logs_and_exceptions
from tkr_utils.app_paths import AppPaths

logger = setup_logging(__file__)


class StoryManager:
    """
    A class to manage story loading and processing operations.

    This class handles both story outlines and generated responses, providing
    functionality to load, validate, and process story data from files.
    """

    def __init__(self) -> None:
        """Initialize StoryManager with required directories."""
        self.story_dir = Path(AppPaths.BASE_DIR) / 'stories' / 'outlines'
        self.data_dir = Path(AppPaths.LOCAL_DATA)
        logger.info(f"Initialized StoryManager with story directory: {self.story_dir}")
        logger.info(f"Using data directory: {self.data_dir}")

    @staticmethod
    def format_story_name(story_data: Dict[str, Any]) -> str:
        """
        Format story name consistently for directory/file naming.

        Args:
            story_data: Story data dictionary containing title

        Returns:
            Formatted story name safe for filesystem use
        """
        # Handle both full story data and title-only data
        title = story_data['story'].get('title', story_data['story'])

        # Convert to lowercase and replace special characters
        name = title.lower()
        # Replace all special characters (including spaces and apostrophes) with underscores
        name = re.sub(r'[^a-z0-9]+', '_', name)

        return name.strip('_')

    @logs_and_exceptions(logger)
    def get_all_stories(self) -> List[Dict[str, Any]]:
        """
        Get all available stories with their responses.

        Returns:
            List of stories with outline data and responses

        Raises:
            FileNotFoundError: If story directory doesn't exist
        """
        stories = []

        if not self.story_dir.exists():
            logger.error(f"Story outline directory not found: {self.story_dir}")
            raise FileNotFoundError(f"Story directory {self.story_dir} does not exist")

        try:
            for story_file in self.story_dir.glob('*.json'):
                try:
                    story_outline = self._load_single_story(story_file.name)
                    if story_outline:
                        # Get formatted story name for response directory
                        story_title = self.format_story_name(
                            {"story": {"title": story_outline['title']}}
                        )
                        response_dir = self.data_dir / story_title

                        # Get responses from each provider
                        responses = {
                            "anthropic": self._process_responses(
                                response_dir / "anthropic",
                                story_outline['hero']
                            ),
                            "openai": self._process_responses(
                                response_dir / "openai",
                                story_outline['hero']
                            )
                        }

                        story_outline['responses'] = responses
                        stories.append(story_outline)
                except Exception as e:
                    logger.error(f"Error processing story {story_file}: {str(e)}")
                    continue

            return stories

        except Exception as e:
            logger.error(f"Error getting all stories: {str(e)}")
            raise

    @logs_and_exceptions(logger)
    def _load_single_story(self, filename: str) -> Optional[Dict[str, Any]]:
        """
        Load a single story with validation and error handling.

        Args:
            filename: Name of the story file to load

        Returns:
            Story data dictionary or None if loading fails
        """
        file_path = self.story_dir / filename

        try:
            with open(file_path, 'r') as f:
                outline_data = json.load(f)

            if not self.validate_story_format(outline_data):
                raise ValueError("Story format validation failed")

            story_id = os.path.splitext(filename)[0]
            story_title = self.format_story_name(outline_data)
            hero_order = outline_data['story']['hero']

            # Get response data maintaining hero order
            response_dir = self.data_dir / story_title
            responses = {
                "anthropic": self._get_provider_responses(
                    response_dir / "anthropic",
                    hero_order
                ),
                "openai": self._get_provider_responses(
                    response_dir / "openai",
                    hero_order
                )
            }

            return {
                'id': story_id,
                'path': str(file_path),
                'title': outline_data['story']['title'],
                'plot': outline_data['story']['plot'],
                'hero': hero_order,
                'responses': responses,
                'errors': {
                    'missing_responses': not any(responses.values()),
                    'providers_missing': [
                        provider for provider, resp in responses.items()
                        if not resp
                    ]
                }
            }

        except FileNotFoundError:
            logger.error(f"Story file not found: {file_path}")
            return None
        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing error in {filename}: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Error reading story file {filename}: {str(e)}")
            return None

    @logs_and_exceptions(logger)
    def _get_provider_responses(
        self,
        provider_dir: Path,
        hero_order: List[str]
    ) -> List[Dict[str, Any]]:
        """
        Get all response files for a specific provider.

        Args:
            provider_dir: Path to provider's response directory
            hero_order: Original ordered list of heroes

        Returns:
            List of response data in original hero order
        """
        responses_map = {}
        if not provider_dir.exists():
            logger.warning(f"Provider directory not found: {provider_dir}")
            return []

        try:
            for response_file in provider_dir.glob("response_*.json"):
                try:
                    with open(response_file, 'r') as f:
                        response_data = json.load(f)

                    if not self._validate_response_format(response_data):
                        logger.warning(f"Invalid response format in {response_file}")
                        continue

                    hero_name = response_data['hero']
                    responses_map[hero_name] = response_data
                    logger.debug(f"Loaded response for hero: {hero_name}")

                except json.JSONDecodeError as e:
                    logger.error(
                        f"Invalid JSON in response file {response_file}: {str(e)}"
                    )
                    continue
                except Exception as e:
                    logger.error(
                        f"Error reading response file {response_file}: {str(e)}"
                    )
                    continue

            # Return responses in original hero order
            ordered_responses = [
                responses_map[hero]
                for hero in hero_order
                if hero in responses_map
            ]
            return ordered_responses

        except Exception as e:
            logger.error(f"Error accessing provider responses: {str(e)}")
            return []

    @logs_and_exceptions(logger)
    def _process_responses(
        self,
        response_dir: Path,
        hero_list: List[str]
    ) -> Dict[str, Any]:
        """
        Process response files for a given provider directory.

        Args:
            response_dir: Path to provider response directory
            hero_list: List of hero names to process

        Returns:
            Dictionary of hero responses and any errors
        """
        responses = {}
        errors = {}

        if not response_dir.exists():
            logger.debug(f"Response directory does not exist: {response_dir}")
            return {"responses": responses, "errors": errors}

        try:
            for hero in hero_list:
                formatted_hero = self.format_story_name({"story": {"title": hero}})
                response_path = response_dir / f"response_{formatted_hero}.json"
                bias_path = response_dir / f"bias_report_{formatted_hero}.json"

                try:
                    if response_path.exists():
                        with open(response_path, 'r', encoding='utf-8') as f:
                            response_data = json.load(f)
                            responses[hero] = response_data
                    else:
                        logger.debug(f"Response file not found for hero {hero}: {response_path}")
                        errors[hero] = f"Response file not found: {response_path}"

                    if bias_path.exists():
                        with open(bias_path, 'r', encoding='utf-8') as f:
                            bias_data = json.load(f)
                            if hero in responses:
                                responses[hero]['bias_report'] = bias_data
                    else:
                        logger.debug(f"Bias report not found for hero {hero}: {bias_path}")
                        if hero not in errors:
                            errors[hero] = []
                        if isinstance(errors[hero], list):
                            errors[hero].append(f"Bias report not found: {bias_path}")
                        else:
                            errors[hero] = [errors[hero], f"Bias report not found: {bias_path}"]

                except Exception as e:
                    logger.error(f"Error processing response for hero {hero}: {str(e)}")
                    errors[hero] = f"Error processing response: {str(e)}"

            return {"responses": responses, "errors": errors}

        except Exception as e:
            logger.error(f"Error processing responses in {response_dir}: {str(e)}")
            return {"responses": responses, "errors": {"general": str(e)}}

    @logs_and_exceptions(logger)
    async def load_story(self, story_path: Path) -> Dict[str, Any]:
        """
        Load story data from a file.

        Args:
            story_path: Path to story file

        Returns:
            Story data dictionary

        Raises:
            FileNotFoundError: If story file doesn't exist
            ValueError: If story data is invalid
        """
        if not story_path.exists():
            raise FileNotFoundError(f"Story file not found: {story_path}")

        try:
            with open(story_path, 'r', encoding='utf-8') as f:
                story_data = json.load(f)

            if not story_data or 'story' not in story_data:
                raise ValueError(f"Invalid story data in {story_path}")

            return story_data

        except json.JSONDecodeError as e:
            logger.error(f"Error decoding JSON from {story_path}: {str(e)}")
            raise ValueError(f"Invalid JSON in story file: {str(e)}")
        except Exception as e:
            logger.error(f"Error loading story from {story_path}: {str(e)}")
            raise

    @staticmethod
    def validate_story_format(story_data: Dict[str, Any]) -> bool:
        """
        Validate that story outline data matches expected format.

        Args:
            story_data: Story data to validate

        Returns:
            True if valid, False otherwise
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

    def _validate_response_format(self, response_data: Dict) -> bool:
        """
        Validate response data matches standardized format.

        Args:
            response_data: Response data to validate

        Returns:
            True if valid, False otherwise
        """
        try:
            # Check required fields
            required_fields = {
                "story_id": str,
                "hero": str,
                "text": str,
                "metadata": dict
            }

            for field, expected_type in required_fields.items():
                if field not in response_data:
                    logger.warning(f"Missing required field: {field}")
                    return False
                if not isinstance(response_data[field], expected_type):
                    logger.warning(
                        f"Invalid type for {field}: expected {expected_type.__name__}, "
                        f"got {type(response_data[field]).__name__}"
                    )
                    return False

            # Validate metadata structure
            metadata = response_data["metadata"]
            required_metadata = {
                "provider": str,
                "model": str,
                "total_tokens": int,
                "generated_at": str
            }

            for field, expected_type in required_metadata.items():
                if field not in metadata:
                    logger.warning(f"Missing metadata field: {field}")
                    return False
                if not isinstance(metadata[field], expected_type):
                    logger.warning(
                        f"Invalid type for metadata.{field}: "
                        f"expected {expected_type.__name__}, "
                        f"got {type(metadata[field]).__name__}"
                    )
                    return False

            return True

        except Exception as e:
            logger.error(f"Error validating response format: {str(e)}")
            return False
