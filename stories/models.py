# stories/models.py
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Any

@dataclass
class StoryResponse:
    """Standard response format for story generations"""
    story_id: str
    hero: str
    text: str  # Now expects plain text instead of JSON
    metadata: Dict[str, Any]  # Changed from Dict[str, str|int] to allow nested dicts
    generated_at: datetime = datetime.now()

    @staticmethod
    def from_anthropic(story_id: str, hero: str, response_data: dict) -> "StoryResponse":
        """Create StoryResponse from Anthropic response"""
        # Preserve existing metadata if present
        metadata = response_data.get("metadata", {}).copy()
        metadata.update({
            "provider": "anthropic",
            "model": response_data.get("metadata", {}).get("model", "unknown"),
            "total_tokens": response_data.get("metadata", {}).get("usage", {}).get("total_tokens", 0)
        })
        return StoryResponse(
            story_id=story_id,
            hero=hero,
            text=response_data.get("text", ""),
            metadata=metadata
        )

    @staticmethod
    def from_openai(story_id: str, hero: str, response_data: dict) -> "StoryResponse":
        """Create StoryResponse from OpenAI response"""
        # Preserve existing metadata if present
        metadata = response_data.get("metadata", {}).copy()
        metadata.update({
            "provider": "openai",
            "model": response_data.get("metadata", {}).get("model", "unknown"),
            "total_tokens": response_data.get("metadata", {}).get("total_tokens", 0)
        })
        return StoryResponse(
            story_id=story_id,
            hero=hero,
            text=response_data.get("text", ""),
            metadata=metadata
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
