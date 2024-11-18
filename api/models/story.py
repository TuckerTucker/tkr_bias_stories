# api/models/story.py
from pydantic import BaseModel, Field
from typing import List, Dict, Optional
from datetime import datetime

class StoryMetadata(BaseModel):
    """Metadata for story responses"""
    provider: str
    model: str
    total_tokens: int
    generated_at: datetime

class StoryResponse(BaseModel):
    """Standard response format for stories"""
    story_id: str
    hero: str
    text: str
    metadata: StoryMetadata

class StoryOutline(BaseModel):
    """Base story structure"""
    id: str
    title: str
    plot: str
    hero: List[str]

class Story(StoryOutline):
    """Complete story with responses"""
    responses: Dict[str, List[StoryResponse]]

class StoryList(BaseModel):
    """List of stories response"""
    stories: List[Story]
