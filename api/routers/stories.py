# api/routers/stories.py
from fastapi import APIRouter, HTTPException
from typing import List, Dict
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

@router.get("/", response_model=StoryList)
async def list_stories():
    """Get all available stories with their responses"""
    try:
        raw_stories = await story_app.list_available_stories()

        # Convert to Pydantic models
        stories = []
        for raw_story in raw_stories:
            # Process responses
            formatted_responses: Dict[str, List[StoryResponse]] = {}

            for provider, provider_responses in raw_story.get('responses', {}).items():
                formatted_responses[provider] = []
                for resp in provider_responses:
                    try:
                        # Create StoryResponse with proper metadata
                        story_response = StoryResponse(
                            story_id=resp.get('story_id', raw_story['id']),
                            hero=resp.get('hero', ''),
                            text=resp.get('text', ''),
                            metadata=StoryMetadata(
                                provider=resp.get('metadata', {}).get('provider', provider),
                                model=resp.get('metadata', {}).get('model', 'unknown'),
                                total_tokens=resp.get('metadata', {}).get('total_tokens', 0),
                                generated_at=datetime.fromisoformat(
                                    resp.get('metadata', {}).get('generated_at', datetime.now().isoformat())
                                )
                            )
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
                hero=raw_story.get('hero', []),
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

        # Process responses
        formatted_responses: Dict[str, List[StoryResponse]] = {}

        for provider, provider_responses in raw_story.get('responses', {}).items():
            formatted_responses[provider] = []
            for resp in provider_responses:
                try:
                    story_response = StoryResponse(
                        story_id=resp.get('story_id', story_id),
                        hero=resp.get('hero', ''),
                        text=resp.get('text', ''),
                        metadata=StoryMetadata(
                            provider=resp.get('metadata', {}).get('provider', provider),
                            model=resp.get('metadata', {}).get('model', 'unknown'),
                            total_tokens=resp.get('metadata', {}).get('total_tokens', 0),
                            generated_at=datetime.fromisoformat(
                                resp.get('metadata', {}).get('generated_at', datetime.now().isoformat())
                            )
                        )
                    )
                    formatted_responses[provider].append(story_response)
                except Exception as e:
                    logger.error(f"Error processing response: {str(e)}")
                    continue

        # Create Story model
        story = Story(
            id=story_id,
            title=raw_story['story']['title'],
            plot=raw_story['story'].get('plot', ''),
            hero=raw_story['story'].get('hero', []),
            responses=formatted_responses
        )

        return story

    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Story {story_id} not found")
    except Exception as e:
        logger.error(f"Error getting story: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
