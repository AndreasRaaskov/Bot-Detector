# test_bluesky_client.py - Unit tests for Bluesky client
# Tests Bluesky AT Protocol integration, authentication, data fetching, and error handling

import pytest
import httpx
import sys
from unittest.mock import AsyncMock, patch, Mock
from datetime import datetime, timezone
from pathlib import Path

# Add backend directory to Python path
backend_dir = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_dir))

from bluesky_client import BlueskyClient, BlueskyProfile, BlueskyPost

class TestBlueskyClientInitialization:
    """
    Test BlueskyClient initialization and setup
    """
    
    def test_client_creation_with_credentials(self):
        """
        Test creating client with username and password
        """
        client = BlueskyClient("test@example.com", "password123")
        
        assert client.username == "test@example.com"
        assert client.password == "password123"
        assert client.session_token is None
        assert client.base_url == "https://bsky.social"
        assert client.client is not None
    
    def test_client_creation_without_credentials(self):
        """
        Test creating client without credentials (read-only mode)
        """
        client = BlueskyClient()
        
        assert client.username is None
        assert client.password is None
        assert client.session_token is None
    
    async def test_client_context_manager(self):
        """
        Test using client as async context manager
        """
        async with BlueskyClient() as client:
            assert client is not None
        # Should automatically close without error

class TestBlueskyAuthentication:
    """
    Test Bluesky authentication functionality
    """
    
    @pytest.mark.asyncio
    async def test_successful_authentication(self):
        """
        Test successful authentication with valid credentials
        """
        client = BlueskyClient("test@example.com", "password123")
        
        # Mock successful authentication response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "accessJwt": "jwt_token_123",
            "did": "did:plc:test123"
        }
        
        with patch.object(client.client, 'post', return_value=mock_response):
            result = await client.authenticate()
        
        assert result is True
        assert client.session_token == "jwt_token_123"
    
    @pytest.mark.asyncio
    async def test_failed_authentication(self):
        """
        Test authentication failure with invalid credentials
        """
        client = BlueskyClient("test@example.com", "wrong_password")
        
        # Mock failed authentication response
        mock_response = Mock()
        mock_response.status_code = 401
        mock_response.text = "Invalid credentials"
        
        with patch.object(client.client, 'post', return_value=mock_response):
            result = await client.authenticate()
        
        assert result is False
        assert client.session_token is None
    
    @pytest.mark.asyncio
    async def test_authentication_without_credentials(self):
        """
        Test authentication attempt without credentials
        """
        client = BlueskyClient()  # No credentials
        
        result = await client.authenticate()
        
        assert result is False
        assert client.session_token is None
    
    @pytest.mark.asyncio
    async def test_authentication_network_error(self):
        """
        Test authentication with network error
        """
        client = BlueskyClient("test@example.com", "password123")
        
        with patch.object(client.client, 'post', side_effect=httpx.RequestError("Network error")):
            result = await client.authenticate()
        
        assert result is False
        assert client.session_token is None
    
    def test_get_headers_without_auth(self):
        """
        Test getting HTTP headers without authentication
        """
        client = BlueskyClient()
        headers = client._get_headers()
        
        assert headers["Content-Type"] == "application/json"
        assert headers["User-Agent"] == "BotDetector/1.0"
        assert "Authorization" not in headers
    
    def test_get_headers_with_auth(self):
        """
        Test getting HTTP headers with authentication token
        """
        client = BlueskyClient()
        client.session_token = "test_token_123"
        headers = client._get_headers()
        
        assert headers["Content-Type"] == "application/json"
        assert headers["User-Agent"] == "BotDetector/1.0"
        assert headers["Authorization"] == "Bearer test_token_123"

class TestBlueskyProfileFetching:
    """
    Test fetching user profiles from Bluesky
    """
    
    @pytest.mark.asyncio
    async def test_get_profile_success(self):
        """
        Test successfully fetching a user profile
        """
        client = BlueskyClient()
        
        # Mock successful profile response
        profile_data = {
            "did": "did:plc:test123456789",
            "handle": "testuser.bsky.social",
            "displayName": "Test User",
            "description": "A test user account",
            "avatar": "https://example.com/avatar.jpg",
            "banner": "https://example.com/banner.jpg",
            "followersCount": 150,
            "followsCount": 200,
            "postsCount": 500,
            "createdAt": "2023-06-15T10:30:00.000Z"
        }
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = profile_data
        
        with patch.object(client.client, 'get', return_value=mock_response):
            profile = await client.get_profile("testuser.bsky.social")
        
        assert profile is not None
        assert isinstance(profile, BlueskyProfile)
        assert profile.handle == "testuser.bsky.social"
        assert profile.display_name == "Test User"
        assert profile.description == "A test user account"
        assert profile.followers_count == 150
        assert profile.follows_count == 200
        assert profile.posts_count == 500
        assert profile.created_at.year == 2023
    
    @pytest.mark.asyncio
    async def test_get_profile_not_found(self):
        """
        Test fetching profile for non-existent user
        """
        client = BlueskyClient()
        
        mock_response = Mock()
        mock_response.status_code = 404
        
        with patch.object(client.client, 'get', return_value=mock_response):
            profile = await client.get_profile("nonexistent.bsky.social")
        
        assert profile is None
    
    @pytest.mark.asyncio
    async def test_get_profile_handle_cleaning(self):
        """
        Test that @ symbols are stripped from handles
        """
        client = BlueskyClient()
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "did": "did:plc:test123",
            "handle": "testuser.bsky.social",
            "followersCount": 100,
            "followsCount": 150,
            "postsCount": 50
        }
        
        with patch.object(client.client, 'get', return_value=mock_response) as mock_get:
            await client.get_profile("@testuser.bsky.social")
        
        # Should have called API with cleaned handle
        call_args = mock_get.call_args
        assert "testuser.bsky.social" in str(call_args)
    
    @pytest.mark.asyncio
    async def test_get_profile_network_error(self):
        """
        Test profile fetching with network error
        """
        client = BlueskyClient()
        
        with patch.object(client.client, 'get', side_effect=httpx.RequestError("Network error")):
            profile = await client.get_profile("testuser.bsky.social")
        
        assert profile is None
    
    def test_parse_datetime_valid(self):
        """
        Test parsing valid datetime strings
        """
        client = BlueskyClient()
        
        # Test ISO format with Z
        dt1 = client._parse_datetime("2023-06-15T10:30:00.000Z")
        assert dt1.year == 2023
        assert dt1.month == 6
        assert dt1.day == 15
        assert dt1.tzinfo is not None
        
        # Test ISO format with timezone
        dt2 = client._parse_datetime("2023-06-15T10:30:00.000+00:00")
        assert dt2.year == 2023
        assert dt2.tzinfo is not None
    
    def test_parse_datetime_invalid(self):
        """
        Test parsing invalid datetime strings
        """
        client = BlueskyClient()
        
        # Test invalid format
        result1 = client._parse_datetime("invalid-date")
        assert result1 is None
        
        # Test None input
        result2 = client._parse_datetime(None)
        assert result2 is None
        
        # Test empty string
        result3 = client._parse_datetime("")
        assert result3 is None

class TestBlueskyPostFetching:
    """
    Test fetching user posts from Bluesky
    """
    
    @pytest.mark.asyncio
    async def test_get_user_posts_success(self, sample_bluesky_profile):
        """
        Test successfully fetching user posts
        """
        client = BlueskyClient()
        
        # Mock profile response
        profile_response = Mock()
        profile_response.status_code = 200
        profile_response.json.return_value = {
            "did": sample_bluesky_profile.did,
            "handle": sample_bluesky_profile.handle,
            "followersCount": 100,
            "followsCount": 200,
            "postsCount": 50
        }
        
        # Mock posts response
        posts_data = {
            "feed": [
                {
                    "post": {
                        "uri": "at://test.user/app.bsky.feed.post/1",
                        "record": {
                            "$type": "app.bsky.feed.post",
                            "text": "This is a test post",
                            "createdAt": "2024-01-15T12:00:00.000Z"
                        },
                        "replyCount": 5,
                        "repostCount": 10,
                        "likeCount": 25
                    }
                },
                {
                    "post": {
                        "uri": "at://test.user/app.bsky.feed.post/2",
                        "record": {
                            "$type": "app.bsky.feed.post",
                            "text": "Another test post",
                            "createdAt": "2024-01-15T13:00:00.000Z",
                            "reply": {"parent": {"uri": "at://other/post"}}  # This is a reply
                        },
                        "replyCount": 2,
                        "repostCount": 3,
                        "likeCount": 8
                    }
                }
            ]
        }
        
        posts_response = Mock()
        posts_response.status_code = 200
        posts_response.json.return_value = posts_data
        
        with patch.object(client.client, 'get', side_effect=[profile_response, posts_response]):
            posts = await client.get_user_posts("testuser.bsky.social")
        
        assert len(posts) == 2
        assert all(isinstance(post, BlueskyPost) for post in posts)
        
        # Check first post
        post1 = posts[0]
        assert post1.text == "This is a test post"
        assert post1.reply_count == 5
        assert post1.repost_count == 10
        assert post1.like_count == 25
        assert not post1.is_reply
        assert not post1.is_repost
        
        # Check second post (reply)
        post2 = posts[1]
        assert post2.text == "Another test post"
        assert post2.is_reply is True
        assert post2.is_repost is False
    
    @pytest.mark.asyncio
    async def test_get_user_posts_profile_not_found(self):
        """
        Test fetching posts when profile doesn't exist
        """
        client = BlueskyClient()
        
        # Mock profile not found
        with patch.object(client, 'get_profile', return_value=None):
            posts = await client.get_user_posts("nonexistent.bsky.social")
        
        assert posts == []
    
    @pytest.mark.asyncio
    async def test_get_user_posts_with_reposts(self):
        """
        Test fetching posts including reposts
        """
        client = BlueskyClient()
        
        # Mock profile response
        profile_response = Mock()
        profile_response.status_code = 200
        profile_response.json.return_value = {
            "did": "did:plc:test123",
            "handle": "testuser.bsky.social",
            "followersCount": 100,
            "followsCount": 200,
            "postsCount": 50
        }
        
        # Mock posts with repost
        posts_data = {
            "feed": [
                {
                    "post": {
                        "uri": "at://test.user/app.bsky.feed.post/1",
                        "record": {
                            "$type": "app.bsky.feed.post",
                            "text": "Original post",
                            "createdAt": "2024-01-15T12:00:00.000Z"
                        },
                        "replyCount": 0,
                        "repostCount": 0,
                        "likeCount": 0
                    },
                    "reason": {
                        "$type": "app.bsky.feed.defs#reasonRepost"
                    }
                }
            ]
        }
        
        posts_response = Mock()
        posts_response.status_code = 200
        posts_response.json.return_value = posts_data
        
        with patch.object(client.client, 'get', side_effect=[profile_response, posts_response]):
            posts = await client.get_user_posts("testuser.bsky.social")
        
        assert len(posts) == 1
        post = posts[0]
        assert post.is_repost is True
    
    @pytest.mark.asyncio
    async def test_get_user_posts_with_limit(self):
        """
        Test fetching posts with custom limit
        """
        client = BlueskyClient()
        
        # Mock successful responses
        with patch.object(client, 'get_profile') as mock_profile, \
             patch.object(client.client, 'get') as mock_get:
            
            mock_profile.return_value = BlueskyProfile(
                did="did:plc:test123",
                handle="testuser.bsky.social",
                display_name=None,
                description=None,
                avatar=None,
                banner=None,
                followers_count=100,
                follows_count=200,
                posts_count=50,
                created_at=None
            )
            
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"feed": []}
            mock_get.return_value = mock_response
            
            await client.get_user_posts("testuser.bsky.social", limit=50)
            
            # Check that limit was passed correctly
            call_args = mock_get.call_args
            assert call_args[1]["params"]["limit"] == 50

class TestBlueskyFollowersAndFollowing:
    """
    Test fetching followers and following lists
    """
    
    @pytest.mark.asyncio
    async def test_get_followers_sample(self):
        """
        Test fetching followers sample
        """
        client = BlueskyClient()
        
        # Mock profile response
        with patch.object(client, 'get_profile') as mock_profile:
            mock_profile.return_value = BlueskyProfile(
                did="did:plc:test123",
                handle="testuser.bsky.social",
                display_name=None,
                description=None,
                avatar=None,
                banner=None,
                followers_count=100,
                follows_count=200,
                posts_count=50,
                created_at=None
            )
            
            # Mock followers response
            followers_data = {
                "followers": [
                    {"handle": "follower1.bsky.social"},
                    {"handle": "follower2.bsky.social"},
                    {"handle": "follower3.bsky.social"}
                ]
            }
            
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = followers_data
            
            with patch.object(client.client, 'get', return_value=mock_response):
                followers = await client.get_followers_sample("testuser.bsky.social")
            
            assert len(followers) == 3
            assert "follower1.bsky.social" in followers
            assert "follower2.bsky.social" in followers
            assert "follower3.bsky.social" in followers
    
    @pytest.mark.asyncio
    async def test_get_following_sample(self):
        """
        Test fetching following sample
        """
        client = BlueskyClient()
        
        # Mock profile response
        with patch.object(client, 'get_profile') as mock_profile:
            mock_profile.return_value = BlueskyProfile(
                did="did:plc:test123",
                handle="testuser.bsky.social",
                display_name=None,
                description=None,
                avatar=None,
                banner=None,
                followers_count=100,
                follows_count=200,
                posts_count=50,
                created_at=None
            )
            
            # Mock following response
            following_data = {
                "follows": [
                    {"handle": "following1.bsky.social"},
                    {"handle": "following2.bsky.social"}
                ]
            }
            
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = following_data
            
            with patch.object(client.client, 'get', return_value=mock_response):
                following = await client.get_following_sample("testuser.bsky.social")
            
            assert len(following) == 2
            assert "following1.bsky.social" in following
            assert "following2.bsky.social" in following
    
    @pytest.mark.asyncio
    async def test_get_followers_profile_not_found(self):
        """
        Test getting followers when profile doesn't exist
        """
        client = BlueskyClient()
        
        with patch.object(client, 'get_profile', return_value=None):
            followers = await client.get_followers_sample("nonexistent.bsky.social")
        
        assert followers == []

class TestBlueskyErrorHandling:
    """
    Test error handling in various scenarios
    """
    
    @pytest.mark.asyncio
    async def test_api_rate_limiting(self):
        """
        Test handling of API rate limiting
        """
        client = BlueskyClient()
        
        # Mock rate limit response
        mock_response = Mock()
        mock_response.status_code = 429  # Too Many Requests
        mock_response.text = "Rate limit exceeded"
        
        with patch.object(client.client, 'get', return_value=mock_response):
            profile = await client.get_profile("testuser.bsky.social")
        
        assert profile is None
    
    @pytest.mark.asyncio
    async def test_api_server_error(self):
        """
        Test handling of server errors
        """
        client = BlueskyClient()
        
        # Mock server error response
        mock_response = Mock()
        mock_response.status_code = 500  # Internal Server Error
        mock_response.text = "Internal server error"
        
        with patch.object(client.client, 'get', return_value=mock_response):
            profile = await client.get_profile("testuser.bsky.social")
        
        assert profile is None
    
    @pytest.mark.asyncio
    async def test_malformed_response_data(self):
        """
        Test handling of malformed response data
        """
        client = BlueskyClient()
        
        # Mock response with missing required fields
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "incomplete": "data"
            # Missing required fields like 'did', 'handle', etc.
        }
        
        with patch.object(client.client, 'get', return_value=mock_response):
            profile = await client.get_profile("testuser.bsky.social")
        
        # Should handle gracefully and return a profile with default values
        assert profile is not None
        assert profile.handle == ""  # Default value when missing

@pytest.mark.unit
class TestBlueskyIntegration:
    """
    Integration-style tests for BlueskyClient
    """
    
    @pytest.mark.asyncio
    async def test_full_user_analysis_workflow(self):
        """
        Test a complete workflow of fetching all data needed for analysis
        """
        client = BlueskyClient("test@example.com", "password123")
        
        # Mock all the API calls needed for a full analysis
        with patch.object(client, 'authenticate', return_value=True), \
             patch.object(client, 'get_profile') as mock_profile, \
             patch.object(client, 'get_user_posts') as mock_posts, \
             patch.object(client, 'get_followers_sample') as mock_followers, \
             patch.object(client, 'get_following_sample') as mock_following:
            
            # Set up mock returns
            mock_profile.return_value = BlueskyProfile(
                did="did:plc:test123",
                handle="testuser.bsky.social",
                display_name="Test User",
                description="Test account",
                avatar=None,
                banner=None,
                followers_count=100,
                follows_count=150,
                posts_count=500,
                created_at=datetime.now(timezone.utc)
            )
            
            mock_posts.return_value = [
                BlueskyPost(
                    uri="at://test/post/1",
                    text="Test post",
                    created_at=datetime.now(timezone.utc),
                    reply_count=1,
                    repost_count=2,
                    like_count=5,
                    is_reply=False,
                    is_repost=False
                )
            ]
            
            mock_followers.return_value = ["follower1.bsky.social", "follower2.bsky.social"]
            mock_following.return_value = ["following1.bsky.social", "following2.bsky.social"]
            
            # Execute full workflow
            auth_success = await client.authenticate()
            profile = await client.get_profile("testuser.bsky.social")
            posts = await client.get_user_posts("testuser.bsky.social")
            followers = await client.get_followers_sample("testuser.bsky.social")
            following = await client.get_following_sample("testuser.bsky.social")
            
            # Verify all operations succeeded
            assert auth_success is True
            assert profile is not None
            assert len(posts) == 1
            assert len(followers) == 2
            assert len(following) == 2
            
            # Verify we have all data needed for bot analysis
            assert profile.followers_count == 100
            assert profile.follows_count == 150
            assert posts[0].text == "Test post"