# api/tests/test_api.py
import asyncio
import pytest
from fastapi.testclient import TestClient
from pathlib import Path
from ..main import app
from tkr_utils.app_paths import AppPaths
from tkr_utils.config_logging import setup_logging

logger = setup_logging(__file__)
client = TestClient(app)

def test_root():
    """Test root endpoint"""
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Bias Stories API"}

def test_list_stories():
    """Test stories listing"""
    response = client.get("/api/stories/")
    assert response.status_code == 200
    data = response.json()
    assert "stories" in data
    # Verify story structure
    for story in data["stories"]:
        assert "id" in story
        assert "title" in story
        assert "plot" in story
        assert "hero" in story

# api/tests/test_api.py
def test_get_story():
    """Test getting specific story"""
    # Use a known existing story file
    story_name = "traffic_stop2"
    story_path = AppPaths.BASE_DIR / "stories" / "outlines" / f"{story_name}.json"

    # Skip test if story file doesn't exist
    if not story_path.exists():
        pytest.skip(f"Story file {story_path} not found")

    response = client.get(f"/api/stories/{story_name}")
    assert response.status_code == 200
    data = response.json()

    # Verify response structure
    assert "id" in data
    assert "title" in data
    assert "plot" in data
    assert "hero" in data
    assert isinstance(data["hero"], list)

def test_get_nonexistent_story():
    """Test getting a story that doesn't exist"""
    response = client.get("/api/stories/nonexistent")
    assert response.status_code == 404
