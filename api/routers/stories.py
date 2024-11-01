# api/routers/stories.py
from fastapi import APIRouter, HTTPException
from typing import List
from pathlib import Path
from ..models.story import StoryList, StoryTemplate, StoryResponse, StoryData
from stories.story_manager import StoryManager
from stories.story_generator import StoryGenerationApp
from tkr_utils.app_paths import AppPaths
from tkr_utils.config_logging import setup_logging

logger = setup_logging(__file__)
router = APIRouter(prefix="/api/stories", tags=["stories"])
story_app = StoryGenerationApp()

@router.get("/", response_model=StoryList)
async def list_stories():
    """Get all available stories"""
    try:
        stories = await story_app.list_available_stories()
        # Convert to response format
        story_responses = [
            StoryResponse(
                id=story['id'],
                title=story['title'],
                plot=story['plot'],
                hero=story['hero']
            )
            for story in stories
        ]
        return StoryList(stories=story_responses)
    except Exception as e:
        logger.error(f"Error listing stories: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{story_name}", response_model=StoryResponse)
async def get_story(story_name: str):
    """Get specific story with variations"""
    try:
        story_path = AppPaths.BASE_DIR / "stories" / "outlines" / f"{story_name}.json"
        if not story_path.exists():
            logger.error(f"Story not found: {story_path}")
            raise FileNotFoundError(f"Story {story_name} not found")

        story_data = await story_app.story_manager.load_story(str(story_path))
        response = StoryResponse.from_story_data(story_data, story_name)
        return response
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Story {story_name} not found")
    except Exception as e:
        logger.error(f"Error getting story: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
