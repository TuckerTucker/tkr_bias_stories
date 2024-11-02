# stories/story_manager.py

import json
import os
from typing import List, Dict, Any, Optional
from pathlib import Path
from tkr_utils.config_logging import setup_logging
from tkr_utils.decorators import logs_and_exceptions
from tkr_utils.app_paths import AppPaths

logger = setup_logging(__file__)

class StoryManager:
    """
    Manages story loading and processing operations.
    Handles both story outlines and generated responses.
    """

    def __init__(self) -> None:
        """Initialize StoryManager with required directories."""
        self.story_dir = os.path.join(AppPaths.BASE_DIR, 'stories', 'outlines')
        self.data_dir = AppPaths.LOCAL_DATA
        logger.info(f"Initialized StoryManager with story directory: {self.story_dir}")
        logger.info(f"Using data directory: {self.data_dir}")

    @staticmethod
    def format_story_name(story_data: Dict[str, Any]) -> str:
        """
        Format story name consistently for directory/file naming by removing special characters
        and standardizing format.

        Args:
            story_data (Dict[str, Any]): Story data dictionary containing title

        Returns:
            str: Formatted story name safe for filesystem use
        """
        import re
        title = story_data['story']['title']

        # Convert to lowercase
        name = title.lower()

        # Replace spaces and special characters with underscores
        # Remove any characters that aren't alphanumeric or underscores
        name = re.sub(r'[^a-z0-9]+', '_', name)

        # Remove leading/trailing underscores
        name = name.strip('_')

        return name

    @logs_and_exceptions(logger)
    def get_all_stories(self) -> List[Dict[str, Any]]:
        """
        Get all available stories with their responses.

        Returns:
            List[Dict[str, Any]]: List of stories with outline data and responses
        """
        stories = []

        # Verify story directory exists
        if not os.path.exists(self.story_dir):
            logger.error(f"Story outline directory not found: {self.story_dir}")
            raise FileNotFoundError(f"Story directory {self.story_dir} does not exist")

        try:
            for filename in os.listdir(self.story_dir):
                if not filename.endswith('.json'):
                    continue

                try:
                    story_outline = self._load_single_story(filename)
                    if story_outline:
                        # Get formatted story name for response directory
                        story_title = self.format_story_name({"story": {"title": story_outline['title']}})
                        response_dir = Path(self.data_dir) / story_title

                        # Get responses from each provider
                        responses = {
                            "anthropic": self._process_responses(response_dir / "anthropic"),
                            "openai": self._process_responses(response_dir / "openai")
                        }

                        story_outline['responses'] = responses
                        stories.append(story_outline)

                except Exception as e:
                    logger.error(f"Error processing story {filename}: {str(e)}")
                    continue

            logger.info(f"Successfully loaded {len(stories)} stories")
            return stories

        except Exception as e:
            logger.error(f"Critical error reading stories: {str(e)}")
            raise

    @logs_and_exceptions(logger)
    def _load_single_story(self, filename: str) -> Optional[Dict[str, Any]]:
        """
        Load a single story with validation and error handling.

        Args:
            filename: Name of story file to load

        Returns:
            Optional[Dict[str, Any]]: Story data if valid, None if invalid
        """
        file_path = os.path.join(self.story_dir, filename)

        # Read and validate outline
        try:
            with open(file_path, 'r') as f:
                outline_data = json.load(f)

            if not self.validate_story_format(outline_data):
                raise ValueError("Story format validation failed")

            story_id = os.path.splitext(filename)[0]
            story_title = self.format_story_name(outline_data)

        except FileNotFoundError:
            logger.error(f"Story file not found: {file_path}")
            return None
        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing error in {filename}: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Error reading story file {filename}: {str(e)}")
            return None

        # Get response data with error handling
        try:
            response_dir = self.data_dir / story_title
            responses = {
                "anthropic": self._get_provider_responses(response_dir / "anthropic"),
                "openai": self._get_provider_responses(response_dir / "openai")
            }

            # Check if we got any responses
            if not any(responses.values()):
                logger.warning(f"No responses found for story: {story_title}")

        except Exception as e:
            logger.error(f"Error loading responses for {story_title}: {str(e)}")
            responses = {"anthropic": [], "openai": []}

        return {
            'id': story_id,
            'path': file_path,
            'title': outline_data['story']['title'],
            'plot': outline_data['story']['plot'],
            'hero': outline_data['story']['hero'],
            'responses': responses,
            'errors': {
                'missing_responses': not any(responses.values()),
                'providers_missing': [
                    provider for provider, resp in responses.items()
                    if not resp
                ]
            }
        }

    @logs_and_exceptions(logger)
    def _get_provider_responses(self, provider_dir: Path) -> List[Dict[str, Any]]:
        """
        Get all response files for a specific provider with enhanced error handling.

        Args:
            provider_dir (Path): Path to provider's response directory

        Returns:
            List[Dict[str, Any]]: List of response data
        """
        responses = []
        if not provider_dir.exists():
            logger.warning(f"Provider directory not found: {provider_dir}")
            return responses

        try:
            for response_file in provider_dir.glob("response_*.json"):
                try:
                    with open(response_file, 'r') as f:
                        response_data = json.load(f)

                    # Validate response format
                    if not self._validate_response_format(response_data):
                        logger.warning(f"Invalid response format in {response_file}")
                        continue

                    responses.append(response_data)
                    logger.debug(f"Loaded response from {response_file}")

                except json.JSONDecodeError as e:
                    logger.error(f"Invalid JSON in response file {response_file}: {str(e)}")
                    continue
                except Exception as e:
                    logger.error(f"Error reading response file {response_file}: {str(e)}")
                    continue

            return responses

        except Exception as e:
            logger.error(f"Error accessing provider responses: {str(e)}")
            return responses

    def _process_responses(self, provider_dir: Path) -> List[Dict]:
        """
        Process response files for a provider directory.

        Args:
            provider_dir (Path): Path to provider response directory

        Returns:
            List[Dict]: List of validated response data
        """
        responses = []

        if not provider_dir.exists():
            return responses

        for response_file in provider_dir.glob("response_*.json"):
            try:
                with open(response_file) as f:
                    response_data = json.load(f)

                if self._validate_response_format(response_data):
                    # Extract the text which might be JSON string
                    text = response_data['text']
                    try:
                        # Try to parse if it's a JSON string
                        parsed_text = json.loads(text)
                        text = parsed_text.get('text', text)
                    except json.JSONDecodeError:
                        # If not JSON, use as is
                        pass

                    responses.append({
                        'story_id': response_data['story_id'],
                        'hero': response_data['hero'],
                        'text': text,
                        'metadata': {
                            'provider': response_data['metadata']['provider'],
                            'model': response_data['metadata']['model'],
                            'total_tokens': response_data['metadata']['total_tokens'],
                            'generated_at': response_data['metadata']['generated_at']
                        }
                    })
                else:
                    logger.warning(f"Invalid response format in {response_file}")

            except Exception as e:
                logger.error(f"Error processing response file {response_file}: {str(e)}")

        return responses

    def _validate_response_format(self, response_data: Dict) -> bool:
        """
        Validate response data matches our standardized format.

        Args:
            response_data: Response data to validate

        Returns:
            bool: True if valid
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
                        f"Invalid type for metadata.{field}: expected {expected_type.__name__}, "
                        f"got {type(metadata[field]).__name__}"
                    )
                    return False

            return True

        except Exception as e:
            logger.error(f"Error validating response format: {str(e)}")
            return False

    @staticmethod
    def validate_story_format(story_data: Dict[str, Any]) -> bool:
        """
        Validates that story outline data matches expected format.

        Args:
            story_data (Dict[str, Any]): Story data to validate

        Returns:
            bool: True if valid, False otherwise
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

    @logs_and_exceptions(logger)
    async def load_story(self, story_path: str) -> Dict[str, Any]:
        """
        Loads a specific story from its JSON file.

        Args:
            story_path (str): Path to the story JSON file

        Returns:
            Dict[str, Any]: Story data dictionary

        Raises:
            FileNotFoundError: If story file doesn't exist
            json.JSONDecodeError: If story file is invalid JSON
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
