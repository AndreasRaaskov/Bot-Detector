# bluesky_client.py - Client for interacting with the Bluesky AT Protocol API
# This file handles all communication with Bluesky's servers to fetch user data
# It abstracts away the complexity of the AT Protocol so other parts of our code can be simpler

import httpx
import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime, timezone
import json
import logging
from dataclasses import dataclass

# Set up logging so we can track what's happening and debug issues
logger = logging.getLogger(__name__)

@dataclass
class BlueskyPost:
    """
    Represents a single post from Bluesky
    Using a dataclass makes it easier to work with post data throughout our application
    """
    uri: str  # Unique identifier for the post
    text: str  # The actual content of the post
    created_at: datetime  # When the post was created
    reply_count: int  # Number of replies to this post
    repost_count: int  # Number of reposts/shares
    like_count: int  # Number of likes
    is_reply: bool  # True if this is a reply to another post
    is_repost: bool  # True if this is a repost of someone else's content
    
@dataclass 
class BlueskyProfile:
    """
    Represents a Bluesky user profile
    Contains all the basic information we need about a user
    """
    did: str  # Decentralized identifier - unique ID for this user
    handle: str  # The human-readable handle (e.g., user.bsky.social)
    display_name: Optional[str]  # User's chosen display name
    description: Optional[str]  # User's bio/description
    avatar: Optional[str]  # URL to profile picture
    banner: Optional[str]  # URL to profile banner image
    followers_count: int  # Number of followers
    follows_count: int  # Number of people this user follows
    posts_count: int  # Total number of posts
    created_at: Optional[datetime]  # When the account was created

class BlueskyClient:
    """
    Client for interacting with the Bluesky AT Protocol
    
    This class handles:
    - Authentication with Bluesky
    - Fetching user profiles
    - Retrieving posts and their metadata
    - Rate limiting and error handling
    """
    
    def __init__(self, username: Optional[str] = None, password: Optional[str] = None):
        """
        Initialize the Bluesky client
        
        Args:
            username: Bluesky username (can be handle or email)
            password: Bluesky password
            
        Note: If no credentials provided, client will work in read-only mode
        with potentially limited access
        """
        self.username = username
        self.password = password
        self.session_token = None  # Will store our authentication token
        self.base_url = "https://bsky.social"  # Main Bluesky API endpoint
        
        # Create an HTTP client with reasonable timeouts
        # This prevents our requests from hanging indefinitely
        self.client = httpx.AsyncClient(
            timeout=30.0,  # 30 second timeout for requests
            limits=httpx.Limits(
                max_keepalive_connections=10,
                max_connections=20
            )
        )
        
    async def authenticate(self) -> bool:
        """
        Authenticate with Bluesky to get an access token
        
        Returns:
            bool: True if authentication successful, False otherwise
            
        Note: Some operations may work without authentication, but we'll have
        lower rate limits and access to less data
        """
        if not self.username or not self.password:
            logger.warning("No credentials provided - using unauthenticated mode")
            return False
        
        # Try different username formats - Bluesky can accept various formats
        username_variants = []
        
        # Start with original username
        original_username = self.username
        username_variants.append(original_username)
        
        # If it starts with @, try without @
        if original_username.startswith('@'):
            username_variants.append(original_username[1:])
        
        # If it doesn't end with .bsky.social, try adding it
        if not original_username.endswith('.bsky.social'):
            base_username = original_username.lstrip('@')
            username_variants.append(f"{base_username}.bsky.social")
        
        # If it ends with .bsky.social, try without it
        if original_username.endswith('.bsky.social'):
            base_username = original_username.replace('.bsky.social', '').lstrip('@')
            username_variants.append(base_username)
        
        # Remove duplicates while preserving order
        seen = set()
        unique_variants = []
        for variant in username_variants:
            if variant not in seen:
                seen.add(variant)
                unique_variants.append(variant)
        
        # Try authentication with each variant
        for variant in unique_variants:
            try:
                # Call Bluesky's authentication endpoint
                response = await self.client.post(
                    f"{self.base_url}/xrpc/com.atproto.server.createSession",
                    json={
                        "identifier": variant,
                        "password": self.password
                    }
                )
                
                if response.status_code == 200:
                    auth_data = response.json()
                    self.session_token = auth_data.get("accessJwt")
                    logger.info(f"Successfully authenticated with Bluesky using identifier: {variant}")
                    # Store the working username format for future use
                    self.username = variant
                    return True
                else:
                    logger.debug(f"Authentication failed for variant '{variant}': {response.status_code}")
                    
            except Exception as e:
                logger.debug(f"Authentication error with variant '{variant}': {e}")
                continue
        
        # If we get here, all variants failed
        logger.error(f"Authentication failed with all username variants: {unique_variants}")
        return False
    
    def _get_headers(self) -> Dict[str, str]:
        """
        Get HTTP headers for API requests
        
        Returns:
            Dict of headers including authentication if available
        """
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "BotDetector/1.0"  # Identify our application
        }
        
        # Add authentication header if we have a token
        if self.session_token:
            headers["Authorization"] = f"Bearer {self.session_token}"
            
        return headers
    
    async def get_profile(self, handle: str) -> Optional[BlueskyProfile]:
        """
        Fetch a user's profile information
        
        Args:
            handle: The Bluesky handle to look up (e.g., "user.bsky.social")
            
        Returns:
            BlueskyProfile object if successful, None if not found or error
        """
        try:
            # Clean up the handle (remove @ if present)
            clean_handle = handle.lstrip('@')
            
            # Make the API request
            response = await self.client.get(
                f"{self.base_url}/xrpc/app.bsky.actor.getProfile",
                headers=self._get_headers(),
                params={"actor": clean_handle}
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # Parse the response into our BlueskyProfile format
                return BlueskyProfile(
                    did=data.get("did", ""),
                    handle=data.get("handle", ""),
                    display_name=data.get("displayName"),
                    description=data.get("description"),
                    avatar=data.get("avatar"),
                    banner=data.get("banner"),
                    followers_count=data.get("followersCount", 0),
                    follows_count=data.get("followsCount", 0),
                    posts_count=data.get("postsCount", 0),
                    created_at=self._parse_datetime(data.get("createdAt"))
                )
            
            elif response.status_code == 404:
                logger.warning(f"User not found: {handle}")
                return None
            else:
                logger.error(f"Error fetching profile: {response.status_code} {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Profile fetch error: {e}")
            return None
    
    async def get_user_posts(self, handle: str, limit: int = 100) -> List[BlueskyPost]:
        """
        Fetch recent posts from a user
        
        Args:
            handle: The Bluesky handle to fetch posts for
            limit: Maximum number of posts to fetch (default 100)
            
        Returns:
            List of BlueskyPost objects
        """
        try:
            clean_handle = handle.lstrip('@')
            posts = []
            
            # Get the user's profile first to get their DID
            profile = await self.get_profile(clean_handle)
            if not profile:
                return posts
            
            # Fetch the user's timeline/posts
            response = await self.client.get(
                f"{self.base_url}/xrpc/app.bsky.feed.getAuthorFeed",
                headers=self._get_headers(),
                params={
                    "actor": profile.did,
                    "limit": min(limit, 100),  # API typically limits to 100 per request
                    "filter": "posts_and_author_threads"  # Get original posts and threads
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                feed = data.get("feed", [])
                
                for item in feed:
                    post_data = item.get("post", {})
                    record = post_data.get("record", {})
                    
                    # Skip if this is not a text post
                    if record.get("$type") != "app.bsky.feed.post":
                        continue
                    
                    # Determine if this is a reply or repost
                    is_reply = "reply" in record
                    is_repost = item.get("reason", {}).get("$type") == "app.bsky.feed.defs#reasonRepost"
                    
                    # Create BlueskyPost object
                    post = BlueskyPost(
                        uri=post_data.get("uri", ""),
                        text=record.get("text", ""),
                        created_at=self._parse_datetime(record.get("createdAt")),
                        reply_count=post_data.get("replyCount", 0),
                        repost_count=post_data.get("repostCount", 0),
                        like_count=post_data.get("likeCount", 0),
                        is_reply=is_reply,
                        is_repost=is_repost
                    )
                    
                    posts.append(post)
            
            else:
                logger.error(f"Error fetching posts: {response.status_code} {response.text}")
            
            return posts
            
        except Exception as e:
            logger.error(f"Post fetch error: {e}")
            return []
    
    async def get_followers_sample(self, handle: str, limit: int = 50) -> List[str]:
        """
        Get a sample of users who follow the given handle
        
        Args:
            handle: The Bluesky handle
            limit: Maximum number of followers to fetch
            
        Returns:
            List of follower handles
        """
        try:
            clean_handle = handle.lstrip('@')
            
            # Get profile to get DID
            profile = await self.get_profile(clean_handle)
            if not profile:
                return []
            
            response = await self.client.get(
                f"{self.base_url}/xrpc/app.bsky.graph.getFollowers",
                headers=self._get_headers(),
                params={
                    "actor": profile.did,
                    "limit": min(limit, 100)
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                followers = data.get("followers", [])
                return [f.get("handle", "") for f in followers if f.get("handle")]
            
            return []
            
        except Exception as e:
            logger.error(f"Followers fetch error: {e}")
            return []
    
    async def get_following_sample(self, handle: str, limit: int = 50) -> List[str]:
        """
        Get a sample of users that the given handle follows
        
        Args:
            handle: The Bluesky handle
            limit: Maximum number of following to fetch
            
        Returns:
            List of handles this user follows
        """
        try:
            clean_handle = handle.lstrip('@')
            
            # Get profile to get DID
            profile = await self.get_profile(clean_handle)
            if not profile:
                return []
            
            response = await self.client.get(
                f"{self.base_url}/xrpc/app.bsky.graph.getFollows",
                headers=self._get_headers(),
                params={
                    "actor": profile.did,
                    "limit": min(limit, 100)
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                follows = data.get("follows", [])
                return [f.get("handle", "") for f in follows if f.get("handle")]
            
            return []
            
        except Exception as e:
            logger.error(f"Following fetch error: {e}")
            return []
    
    def _parse_datetime(self, dt_string: Optional[str]) -> Optional[datetime]:
        """
        Parse a datetime string from the API into a Python datetime object
        
        Args:
            dt_string: ISO format datetime string
            
        Returns:
            datetime object or None if parsing fails
        """
        if not dt_string:
            return None
            
        try:
            # Parse ISO format datetime and ensure it has timezone info
            dt = datetime.fromisoformat(dt_string.replace('Z', '+00:00'))
            return dt
        except Exception as e:
            logger.warning(f"Could not parse datetime '{dt_string}': {e}")
            return None
    
    async def close(self):
        """
        Clean up the HTTP client
        Call this when you're done using the client to free up resources
        """
        await self.client.aclose()
    
    async def __aenter__(self):
        """
        Support for async context manager (async with statement)
        """
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """
        Support for async context manager - automatically clean up
        """
        await self.close()