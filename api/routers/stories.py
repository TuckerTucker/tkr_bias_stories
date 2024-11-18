# api/routers/stories.py
from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import List, Dict, Any
from pathlib import Path
from datetime import datetime

from ..models.story import (
    StoryList,
    Story,
    StoryResponse,
    StoryOutline,
    StoryMetadata
)
from stories.story_manager import StoryManager
from stories.story_generator import StoryGenerationApp
from tkr_utils.app_paths import AppPaths
from tkr_utils.config_logging import setup_logging

logger = setup_logging(__file__)
router = APIRouter(prefix="/api/stories", tags=["stories"])
story_app = StoryGenerationApp()

def process_response(resp: Dict[str, Any], story_id: str, provider: str) -> StoryResponse:
    """Process individual response with proper error handling.

    Args:
        resp: Raw response dictionary
        story_id: ID of the story
        provider: Provider name (anthropic/openai)

    Returns:
        StoryResponse: Processed response object
    """
    return StoryResponse(
        story_id=resp.get('story_id', story_id),
        hero=resp.get('hero', ''),
        text=resp.get('text', ''),
        metadata=StoryMetadata(
            provider=resp.get('metadata', {}).get('provider', provider),
            model=resp.get('metadata', {}).get('model', 'unknown'),
            total_tokens=resp.get('metadata', {}).get('total_tokens', 0),
            generated_at=datetime.fromisoformat(
                resp.get('metadata', {}).get('generated_at',
                datetime.now().isoformat())
            )
        )
    )

@router.post("/{story_id}/generate", status_code=202)
async def generate_story(story_id: str, background_tasks: BackgroundTasks):
    """Generate new story responses using both OpenAI and Anthropic

    Args:
        story_id: ID of the story to generate
        background_tasks: FastAPI background tasks handler

    Returns:
        Dict with status message

    Raises:
        HTTPException: If story not found or generation fails
    """
    try:
        # Verify story exists
        story_path: Path = Path(AppPaths.BASE_DIR) / "stories" / "outlines" / f"{story_id}.json"
        if not story_path.exists():
            raise HTTPException(
                status_code=404,
                detail=f"Story {story_id} not found"
            )

        # Add generation tasks to background queue
        background_tasks.add_task(
            story_app.generate_all_variations_openai,
            f"{story_id}.json"
        )
        background_tasks.add_task(
            story_app.generate_all_variations_anthropic,
            f"{story_id}.json"
        )

        logger.info(f"Story generation initiated for {story_id}")
        return {
            "status": "initiated",
            "message": f"Story generation started for {story_id}"
        }

    except HTTPException:
        raise
    except Exception as e:
        error_msg = f"Error initiating story generation: {str(e)}"
        logger.error(error_msg)
        raise HTTPException(status_code=500, detail=error_msg)

@router.get("/", response_model=StoryList)
async def list_stories():
    """Get all available stories with their responses"""
    try:
        raw_stories = await story_app.list_available_stories()
        stories: List[Story] = []

        for raw_story in raw_stories:
            formatted_responses: Dict[str, List[StoryResponse]] = {}
            responses = raw_story.get('responses', {})

            if isinstance(responses, dict):
                for provider, provider_responses in responses.items():
                    formatted_responses[provider] = []
                    if isinstance(provider_responses, list):
                        for resp in provider_responses:
                            try:
                                story_response = process_response(
                                    resp, raw_story['id'], provider
                                )
                                formatted_responses[provider].append(story_response)
                            except Exception as e:
                                logger.error(f"Error processing response: {str(e)}")
                                continue

            # Create Story model
            story = Story(
                id=raw_story['id'],
                title=raw_story['title'],
                plot=raw_story.get('plot', ''),
                hero=raw_story.get('hero', []) if isinstance(raw_story.get('hero'), list) else [],
                responses=formatted_responses
            )
            stories.append(story)

        return StoryList(stories=stories)

    except Exception as e:
        logger.error(f"Error listing stories: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{story_id}", response_model=Story)
async def get_story(story_id: str):
    """Get specific story with all its responses"""
    try:
        story_path = AppPaths.BASE_DIR / "stories" / "outlines" / f"{story_id}.json"
        if not story_path.exists():
            raise FileNotFoundError(f"Story {story_id} not found")

        raw_story = await story_app.story_manager.load_story(str(story_path))
        formatted_responses: Dict[str, List[StoryResponse]] = {}

        if isinstance(raw_story, dict) and 'responses' in raw_story:
            responses = raw_story.get('responses', {})
            if isinstance(responses, dict):
                for provider, provider_responses in responses.items():
                    formatted_responses[provider] = []
                    if isinstance(provider_responses, list):
                        for resp in provider_responses:
                            try:
                                story_response = process_response(
                                    resp, story_id, provider
                                )
                                formatted_responses[provider].append(story_response)
                            except Exception as e:
                                logger.error(f"Error processing response: {str(e)}")
                                continue

        # Create Story model with type checking
        story_data = raw_story.get('story', {})
        if not isinstance(story_data, dict):
            raise ValueError("Invalid story data format")

        story = Story(
            id=story_id,
            title=story_data.get('title', ''),
            plot=story_data.get('plot', ''),
            hero=story_data.get('hero', []) if isinstance(story_data.get('hero'), list) else [],
            responses=formatted_responses
        )

        return story

    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Story {story_id} not found")
    except Exception as e:
        logger.error(f"Error getting story: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
