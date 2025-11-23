# models.py - Data models for API requests and responses
# This file defines the structure of data that flows in and out of our API
# We use Pydantic models which provide automatic validation and documentation

from pydantic import BaseModel, Field, field_validator, ConfigDict
from typing import Dict, List, Optional, Union
from datetime import datetime

class UserAnalysisRequest(BaseModel):
    """
    Request model for analyzing a user
    This defines what data clients must send when requesting an analysis
    """
    bluesky_handle: str = Field(
        ...,  # Required field
        description="The Bluesky handle to analyze (e.g., 'user.bsky.social' or '@user.bsky.social')",
        json_schema_extra={"example": "example.bsky.social"}
    )
    
    @field_validator('bluesky_handle')
    @classmethod
    def validate_handle(cls, v):
        """
        Validate the Bluesky handle format
        This ensures we get properly formatted handles before processing
        """
        # Remove @ symbol if present (users might include it)
        if v.startswith('@'):
            v = v[1:]
        
        # Handle must not be empty after cleaning
        if not v or v.strip() == '':
            raise ValueError('Bluesky handle cannot be empty')
        
        # Handle should not be just @ symbol
        if v == '':
            raise ValueError('Bluesky handle cannot be just @ symbol')
        
        # Basic validation - handle should contain a dot (domain structure)
        if '.' not in v:
            raise ValueError('Bluesky handle must include domain (e.g., user.bsky.social)')
        
        # Check for valid domain structure - should have text before and after the dot
        parts = v.split('.')
        if len(parts) < 2:
            raise ValueError('Bluesky handle must include domain (e.g., user.bsky.social)')
        
        # Each part should not be empty
        for part in parts:
            if not part or part.strip() == '':
                raise ValueError('Invalid handle format - empty domain parts not allowed')
        
        # Handle should not start or end with dots
        if v.startswith('.') or v.endswith('.'):
            raise ValueError('Bluesky handle cannot start or end with a dot')
        
        # Handle should not have consecutive dots
        if '..' in v:
            raise ValueError('Bluesky handle cannot contain consecutive dots')
        
        return v.lower()  # Convert to lowercase for consistency

class FollowAnalysisResult(BaseModel):
    """
    Results from follower/following ratio analysis
    This helps detect accounts that follow many but have few followers (potential bots)
    """
    follower_count: int = Field(description="Number of accounts following this user")
    following_count: int = Field(description="Number of accounts this user follows")
    ratio: Optional[float] = Field(description="Following/follower ratio (null if invalid, higher values more suspicious)")
    score: float = Field(description="Bot likelihood score from 0-1 based on ratio", ge=0, le=1)
    explanation: str = Field(description="Human-readable explanation of the analysis")

class PostingPatternResult(BaseModel):
    """
    Results from posting pattern analysis
    This detects unnatural posting behaviors like posting too frequently or at odd hours
    """
    total_posts: int = Field(description="Total number of posts analyzed")
    posts_per_day_avg: float = Field(description="Average posts per day")
    posting_hours: List[int] = Field(description="Hours of day when user typically posts (0-23)")
    unusual_frequency: bool = Field(description="True if posting frequency seems unnatural")
    score: float = Field(description="Bot likelihood score from 0-1 based on patterns", ge=0, le=1)
    explanation: str = Field(description="Human-readable explanation of the analysis")

class TextAnalysisResult(BaseModel):
    """
    Results from text content analysis
    This includes perplexity scores and other linguistic indicators
    """
    sample_posts: List[str] = Field(description="Sample of original posts used for analysis")
    avg_perplexity: float = Field(description="Average perplexity score (higher = more human-like)")
    repetitive_content: bool = Field(description="True if content appears repetitive")
    score: float = Field(description="Bot likelihood score from 0-1 based on text analysis", ge=0, le=1)
    explanation: str = Field(description="Human-readable explanation of the analysis")

class LLMAnalysisResult(BaseModel):
    """
    Results from LLM-based analysis
    This is where we ask an AI model to judge if content seems AI-generated
    """
    model_used: str = Field(description="Which LLM model performed the analysis")
    confidence: Optional[float] = Field(None, description="Model's confidence in its assessment (null if analysis skipped/failed)", ge=0, le=1)
    reasoning: str = Field(description="Model's explanation of its decision")
    score: Optional[float] = Field(None, description="Bot likelihood score from 0-1 based on LLM analysis (null if analysis skipped/failed)", ge=0, le=1)
    status: Optional[str] = Field(None, description="Status of the analysis (e.g., 'success', 'skipped', 'failed')")
    error_code: Optional[str] = Field(None, description="Error code if analysis failed or was skipped (e.g., 'LLM_DISABLED', 'API_ERROR')")

class UserAnalysisResponse(BaseModel):
    """
    Complete response containing all analysis results
    This is what gets returned to the client after analysis is complete
    """
    # Basic user information
    handle: str = Field(description="The analyzed Bluesky handle")
    display_name: Optional[str] = Field(description="User's display name")
    bio: Optional[str] = Field(description="User's bio/description")
    avatar_url: Optional[str] = Field(description="URL to user's avatar image")
    created_at: Optional[datetime] = Field(description="When the account was created")
    
    # Analysis results from each detection method
    follow_analysis: FollowAnalysisResult
    posting_pattern: PostingPatternResult
    text_analysis: TextAnalysisResult
    llm_analysis: LLMAnalysisResult
    
    # Overall scoring
    overall_score: float = Field(
        description="Combined bot likelihood score from 0-1 (1 = definitely bot)",
        ge=0,
        le=1
    )
    confidence: float = Field(
        description="Confidence in the overall assessment",
        ge=0,
        le=1
    )
    
    # Summary and recommendations
    summary: str = Field(description="Human-readable summary of findings")
    recommendations: List[str] = Field(description="List of recommendations or red flags")
    
    # Metadata
    analysis_timestamp: datetime = Field(default_factory=datetime.now)
    processing_time_ms: Optional[int] = Field(description="Time taken to complete analysis")

class APIKeyConfig(BaseModel):
    """
    Configuration model for API keys
    This helps us manage different LLM service credentials
    """
    model_config = ConfigDict(
        # Hide sensitive fields when converting to dict/JSON
        # This prevents API keys from being accidentally logged or exposed
        extra="forbid"  # Reject unknown fields
    )
    
    openai_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    google_api_key: Optional[str] = None
    bluesky_username: Optional[str] = None
    bluesky_password: Optional[str] = None
        
class ErrorResponse(BaseModel):
    """
    Standard error response format
    This ensures all errors are returned in a consistent format
    """
    error: str = Field(description="Error type or category")
    message: str = Field(description="Human-readable error message")
    details: Optional[Dict] = Field(description="Additional error details")
    timestamp: datetime = Field(default_factory=datetime.now)