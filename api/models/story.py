# api/models/story.py
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from datetime import datetime

class StoryBase(BaseModel):
    """Base story schema"""
    id: str
    title: str
    plot: str
    hero: List[str]

class StoryData(BaseModel):
    """Schema for story data"""
    story: StoryBase

class StoryResponse(BaseModel):
    """Schema for story response"""
    id: str
    title: str
    plot: str
    hero: List[str]

    @classmethod
    def from_story_data(cls, story_data: Dict[str, Any], story_id: str) -> "StoryResponse":
        """Convert story data to response format"""
        return cls(
            id=story_id,
            title=story_data['story']['title'],
            plot=story_data['story']['plot'],
            hero=story_data['story']['hero']
        )

class StoryTemplate(StoryBase):
    """Schema for story template"""
    created_at: datetime = datetime.now()

class StoryList(BaseModel):
    """Schema for list of stories"""
    stories: List[StoryResponse]
