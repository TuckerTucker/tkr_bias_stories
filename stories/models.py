# stories/models.py
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Optional

@dataclass
class StoryResponse:
    """Standard response format for story generations"""
    story_id: str
    hero: str
    text: str
    metadata: Dict[str, str|int]
    generated_at: datetime = datetime.now()

    @staticmethod
    def from_anthropic(story_id: str, hero: str, response_data: Dict) -> "StoryResponse":
        """Create StoryResponse from Anthropic format"""
        story_data = response_data.get("story", {})
        metadata = story_data.get("metadata", {})

        return StoryResponse(
            story_id=story_id,
            hero=hero,
            text=story_data.get("response", {}).get("text", ""),
            metadata={
                "provider": "anthropic",
                "model": metadata.get("model", "unknown"),
                "total_tokens": metadata.get("usage", {}).get("total_tokens", 0)
            }
        )

    @staticmethod
    def from_openai(story_id: str, hero: str, response_data: Dict) -> "StoryResponse":
        """Create StoryResponse from OpenAI format"""
        story_data = response_data.get("story", {})

        return StoryResponse(
            story_id=story_id,
            hero=hero,
            text=story_data.get("response", {}).get("text", ""),
            metadata={
                "provider": "openai",
                "model": story_data.get("llm", {}).get("model", "unknown"),
                "total_tokens": story_data.get("metadata", {}).get("usage", {}).get("total_tokens", 0)
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
