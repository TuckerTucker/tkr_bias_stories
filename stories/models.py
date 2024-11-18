# stories/models.py
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Optional

@dataclass
class StoryResponse:
    """Standard response format for story generations"""
    story_id: str
    hero: str
    text: str  # Now expects plain text instead of JSON
    metadata: Dict[str, str|int]
    generated_at: datetime = datetime.now()

    @staticmethod
    def from_anthropic(story_id: str, hero: str, response_data: dict) -> "StoryResponse":
        """Create StoryResponse from Anthropic response"""
        return StoryResponse(
            story_id=story_id,
            hero=hero,
            text=response_data.get("text", ""),
            metadata={
                "provider": "anthropic",
                "model": response_data.get("metadata", {}).get("model", "unknown"),
                "total_tokens": response_data.get("metadata", {}).get("usage", {}).get("total_tokens", 0)
            }
        )

    @staticmethod
    def from_openai(story_id: str, hero: str, response_data: dict) -> "StoryResponse":
        """Create StoryResponse from OpenAI response"""
        return StoryResponse(
            story_id=story_id,
            hero=hero,
            text=response_data.get("text", ""),
            metadata={
                "provider": "openai",
                "model": response_data.get("metadata", {}).get("model", "unknown"),
                "total_tokens": response_data.get("metadata", {}).get("total_tokens", 0)
            }
        )

    def to_dict(self) -> Dict:
        """Convert to dictionary format for storage/transmission"""
        return {
            "story_id": self.story_id,
            "hero": self.hero,
            "text": self.text,
            "metadata": self.metadata,
            "generated_at": self.generated_at.isoformat()
        }
