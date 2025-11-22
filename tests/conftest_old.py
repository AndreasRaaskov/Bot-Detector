# conftest.py - Pytest configuration and shared fixtures
# This file contains test fixtures that are shared across all test files
# It helps avoid code duplication and provides consistent test data

import pytest
import asyncio
import tempfile
import json
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime, timezone
from typing import Dict, List, Optional

# Import our modules for testing
from config import Config
from bluesky_client import BlueskyProfile, BlueskyPost
from models import (
    FollowAnalysisResult,
    PostingPatternResult,
    TextAnalysisResult,
    LLMAnalysisResult,
    UserAnalysisResponse
)

# =================================================================
# PYTEST CONFIGURATION
# =================================================================

def pytest_configure(config):
    """Configure pytest with custom markers for different test types"""
    config.addinivalue_line(
        "markers", "unit: mark test as a unit test"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as an integration test"
    )
    config.addinivalue_line(
        "markers", "api: mark test as an API test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )

@pytest.fixture(scope="session")
def event_loop():
    """
    Create an event loop for the entire test session
    This ensures async tests work properly
    """
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

# =================================================================
# CONFIGURATION FIXTURES
# =================================================================

@pytest.fixture
def temp_dir():
    """
    Create a temporary directory for test files
    Automatically cleaned up after the test
    """
    with tempfile.TemporaryDirectory() as tmp_dir:
        yield Path(tmp_dir)

@pytest.fixture
def sample_config_data():
    """
    Sample configuration data for testing
    Contains valid but fake API keys and settings
    """
    return {
        "bluesky": {
            "username": "test_user.bsky.social",
            "password": "test_password_123"
        },
        "llm": {
            "openai_api_key": "sk-test_openai_key_12345",
            "anthropic_api_key": "sk-ant-test_anthropic_key_12345",
            "google_api_key": "test_google_key_12345",
            "preferred_provider": "openai"
        },
        "api": {
            "host": "127.0.0.1",
            "port": 8001,
            "debug": True
        }
    }

@pytest.fixture
def config_json_file(temp_dir, sample_config_data):
    """
    Create a temporary config.json file for testing
    """
    config_file = temp_dir / "config.json"
    with open(config_file, 'w') as f:
        json.dump(sample_config_data, f)
    return config_file

@pytest.fixture
def env_folder_config(temp_dir, sample_config_data):
    """
    Create a temporary .env folder with config.json for testing
    """
    env_dir = temp_dir / ".env"
    env_dir.mkdir()
    config_file = env_dir / "config.json"
    with open(config_file, 'w') as f:
        json.dump(sample_config_data, f)
    return config_file

@pytest.fixture
def env_file(temp_dir):
    """
    Create a temporary .env file for testing
    """
    env_file = temp_dir / ".env"
    env_content = """
BLUESKY_USERNAME=env_test_user.bsky.social
BLUESKY_PASSWORD=env_test_password_456
OPENAI_API_KEY=sk-env_test_openai_key_67890
ANTHROPIC_API_KEY=sk-ant-env_test_anthropic_key_67890
PREFERRED_LLM_PROVIDER=anthropic
API_HOST=0.0.0.0
API_PORT=8002
DEBUG_MODE=false
"""
    with open(env_file, 'w') as f:
        f.write(env_content.strip())
    return env_file

# =================================================================
# BLUESKY DATA FIXTURES
# =================================================================

@pytest.fixture
def sample_bluesky_profile():
    """
    Create a sample Bluesky profile for testing
    Represents a typical user account
    """
    return BlueskyProfile(
        did="did:plc:test123456789",
        handle="testuser.bsky.social",
        display_name="Test User",
        description="Just a test account for bot detection testing",
        avatar="https://example.com/avatar.jpg",
        banner="https://example.com/banner.jpg",
        followers_count=150,
        follows_count=200,
        posts_count=500,
        created_at=datetime(2023, 6, 15, 10, 30, 0, tzinfo=timezone.utc)
    )

@pytest.fixture
def suspicious_bluesky_profile():
    """
    Create a suspicious Bluesky profile for testing bot detection
    Has characteristics that should trigger bot detection alerts
    """
    return BlueskyProfile(
        did="did:plc:suspicious123456",
        handle="botlike.bsky.social",
        display_name="Generic User 12345",
        description="I am a normal human user who enjoys human activities",
        avatar=None,
        banner=None,
        followers_count=5,
        follows_count=2500,  # Very high following to follower ratio
        posts_count=10000,
        created_at=datetime(2024, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
    )

@pytest.fixture
def sample_bluesky_posts():
    """
    Create sample Bluesky posts for testing
    Mix of original posts, replies, and reposts
    """
    base_time = datetime(2024, 1, 15, 12, 0, 0, tzinfo=timezone.utc)
    
    posts = []
    
    # Original posts
    for i in range(10):
        posts.append(BlueskyPost(
            uri=f"at://test.user/app.bsky.feed.post/{i}",
            text=f"This is test post number {i}. Just sharing some thoughts about topic {i}.",
            created_at=base_time.replace(hour=base_time.hour + i),
            reply_count=i,
            repost_count=i * 2,
            like_count=i * 3,
            is_reply=False,
            is_repost=False
        ))
    
    # Some replies
    for i in range(3):
        posts.append(BlueskyPost(
            uri=f"at://test.user/app.bsky.feed.post/reply_{i}",
            text=f"Great point! I totally agree with this perspective on topic {i}.",
            created_at=base_time.replace(hour=base_time.hour + 10 + i),
            reply_count=0,
            repost_count=0,
            like_count=i,
            is_reply=True,
            is_repost=False
        ))
    
    # Some reposts
    for i in range(2):
        posts.append(BlueskyPost(
            uri=f"at://test.user/app.bsky.feed.post/repost_{i}",
            text="",  # Reposts typically have no text
            created_at=base_time.replace(hour=base_time.hour + 13 + i),
            reply_count=0,
            repost_count=0,
            like_count=0,
            is_reply=False,
            is_repost=True
        ))
    
    return posts

@pytest.fixture
def suspicious_bluesky_posts():
    """
    Create suspicious Bluesky posts that should trigger bot detection
    Very repetitive content with suspicious patterns
    """
    base_time = datetime(2024, 1, 15, 0, 0, 0, tzinfo=timezone.utc)
    posts = []
    
    # Very similar posts posted at regular intervals
    template = "As an AI language model, I think {} is very interesting. What do you think about {}?"
    topics = ["technology", "science", "politics", "sports", "music"] * 4
    
    for i, topic in enumerate(topics[:20]):
        posts.append(BlueskyPost(
            uri=f"at://suspicious.user/app.bsky.feed.post/{i}",
            text=template.format(topic, topic),
            created_at=base_time.replace(minute=i * 3),  # Every 3 minutes
            reply_count=0,
            repost_count=0,
            like_count=1,
            is_reply=False,
            is_repost=False
        ))
    
    return posts

# =================================================================
# ANALYZER RESULT FIXTURES
# =================================================================

@pytest.fixture
def sample_follow_analysis():
    """Sample follow analysis result for a normal user"""
    return FollowAnalysisResult(
        follower_count=150,
        following_count=200,
        ratio=1.33,
        score=0.1,
        explanation="Normal follow pattern: 200 following, 150 followers"
    )

@pytest.fixture
def suspicious_follow_analysis():
    """Sample follow analysis result for a suspicious user"""
    return FollowAnalysisResult(
        follower_count=5,
        following_count=2500,
        ratio=500.0,
        score=0.9,
        explanation="Account follows 2,500 and has 5 followers (ratio 500.0:1). Concerns: High follow ratio (500.0:1), Following 2,500 accounts (very high)."
    )

@pytest.fixture
def sample_posting_pattern():
    """Sample posting pattern result for normal posting"""
    return PostingPatternResult(
        total_posts=15,
        posts_per_day_avg=2.5,
        posting_hours=[9, 10, 11, 14, 15, 16, 19, 20, 21],
        unusual_frequency=False,
        score=0.2,
        explanation="Analyzed 15 posts averaging 2.5 posts per day. Posts during hours 9:00-21:00. Posting patterns appear normal for human behavior."
    )

@pytest.fixture
def sample_text_analysis():
    """Sample text analysis result for normal content"""
    return TextAnalysisResult(
        sample_posts=["This is a normal post", "Another regular update", "Sharing some thoughts"],
        avg_perplexity=45.2,
        repetitive_content=False,
        score=0.15,
        explanation="Analyzed 10 original posts with average length 8.5 words. Vocabulary diversity: 75%. Text patterns appear normal for human writing."
    )

@pytest.fixture
def sample_llm_analysis():
    """Sample LLM analysis result for human content"""
    return LLMAnalysisResult(
        model_used="openai/gpt-4o-mini",
        confidence=0.8,
        reasoning="Content shows natural human writing patterns with personal opinions and varied language use.",
        score=0.2
    )

# =================================================================
# MOCK FIXTURES
# =================================================================

@pytest.fixture
def mock_bluesky_client():
    """
    Create a mock Bluesky client for testing
    Avoids making real API calls during tests
    """
    client = AsyncMock()
    
    # Configure common mock responses
    client.authenticate.return_value = True
    client.get_profile.return_value = None  # Will be configured per test
    client.get_user_posts.return_value = []  # Will be configured per test
    client.get_followers_sample.return_value = []
    client.get_following_sample.return_value = []
    client.close = AsyncMock()
    
    return client

@pytest.fixture
def mock_llm_analyzer():
    """
    Create a mock LLM analyzer for testing
    Avoids making real LLM API calls during tests
    """
    analyzer = AsyncMock()
    
    # Default mock response
    mock_result = LLMAnalysisResult(
        model_used="mock/test-model",
        confidence=0.7,
        reasoning="Mock analysis result",
        score=0.3
    )
    analyzer.analyze_content.return_value = mock_result
    analyzer.close = AsyncMock()
    
    return analyzer

# =================================================================
# API TEST FIXTURES
# =================================================================

@pytest.fixture
async def test_client(sample_config_data):
    """
    Create a test client for FastAPI endpoint testing
    """
    # This fixture will be used by API tests
    # Import here to avoid circular imports
    from fastapi.testclient import TestClient
    from main import app
    
    # Override the bot detector with a mock for testing
    return TestClient(app)

@pytest.fixture
def sample_analysis_response(sample_bluesky_profile, sample_follow_analysis, 
                           sample_posting_pattern, sample_text_analysis, 
                           sample_llm_analysis):
    """
    Create a complete sample analysis response for testing
    """
    return UserAnalysisResponse(
        handle=sample_bluesky_profile.handle,
        display_name=sample_bluesky_profile.display_name,
        bio=sample_bluesky_profile.description,
        avatar_url=sample_bluesky_profile.avatar,
        created_at=sample_bluesky_profile.created_at,
        follow_analysis=sample_follow_analysis,
        posting_pattern=sample_posting_pattern,
        text_analysis=sample_text_analysis,
        llm_analysis=sample_llm_analysis,
        overall_score=0.18,  # Weighted average of individual scores
        confidence=0.75,
        summary="Analysis of @testuser.bsky.social indicates this account is likely human (risk level: LOW, score: 0.18/1.00).",
        recommendations=["✅ Account appears to show normal human behavior patterns"],
        processing_time_ms=1250
    )

# =================================================================
# UTILITY FIXTURES
# =================================================================

@pytest.fixture
def clean_environment(monkeypatch):
    """
    Clean environment variables for testing
    Ensures tests don't pick up real environment variables
    """
    env_vars_to_clear = [
        'BLUESKY_USERNAME', 'BLUESKY_PASSWORD',
        'OPENAI_API_KEY', 'ANTHROPIC_API_KEY', 'GOOGLE_API_KEY',
        'PREFERRED_LLM_PROVIDER', 'API_HOST', 'API_PORT', 'DEBUG_MODE'
    ]
    
    for var in env_vars_to_clear:
        monkeypatch.delenv(var, raising=False)
    
    yield

@pytest.fixture
def mock_datetime():
    """
    Mock datetime for consistent test results
    """
    from unittest.mock import patch
    
    fixed_time = datetime(2024, 1, 15, 12, 0, 0, tzinfo=timezone.utc)
    
    with patch('datetime.datetime') as mock_dt:
        mock_dt.now.return_value = fixed_time
        mock_dt.side_effect = lambda *args, **kw: datetime(*args, **kw)
        yield mock_dt