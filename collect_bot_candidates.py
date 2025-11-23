#!/usr/bin/env python3
"""
Bot Candidate Collection Script

This script crawls Bluesky to find accounts with high bot-probability indicators
and stores them in the database for analysis.

Usage:
    python scripts/collect_bot_candidates.py [--target 1000] [--resume]

Features:
- Crawls followers of high-profile seed accounts
- Filters for suspicious bot-like characteristics
- Stores candidates in database
- Progress tracking and resume capability
- Rate limiting to respect API limits
"""

import asyncio
import json
import logging
import os
import sys
from pathlib import Path
from typing import List, Dict, Set, Optional
from datetime import datetime, timedelta, timezone
import re

# Add parent directory to path so we can import backend modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.bluesky_client import BlueskyClient, BlueskyProfile
from backend.database import BotDetectionDB

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('scripts/bot_collection.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class BotCandidateCollector:
    """
    Collects Bluesky accounts with high bot-probability characteristics
    """

    def __init__(
        self,
        db: BotDetectionDB,
        client: BlueskyClient,
        target_count: int = 1000,
        progress_file: str = "scripts/collection_progress.json"
    ):
        self.db = db
        self.client = client
        self.target_count = target_count
        self.progress_file = progress_file

        # Track progress
        self.candidates_found: Set[str] = set()
        self.processed_seeds: Set[str] = set()
        self.analyzed_handles: Set[str] = set()

        # Load existing progress if available
        self._load_progress()

        # Load existing handles from database to avoid re-processing
        self._load_existing_from_database()

    def _load_progress(self):
        """Load progress from previous run if available"""
        if os.path.exists(self.progress_file):
            try:
                with open(self.progress_file, 'r') as f:
                    data = json.load(f)
                    self.candidates_found = set(data.get('candidates_found', []))
                    self.processed_seeds = set(data.get('processed_seeds', []))
                    self.analyzed_handles = set(data.get('analyzed_handles', []))
                    logger.info(f"Resumed: {len(self.candidates_found)} candidates, "
                              f"{len(self.processed_seeds)} seeds processed")
            except Exception as e:
                logger.error(f"Error loading progress: {e}")

    def _load_existing_from_database(self):
        """Load existing handles from database to avoid wasting API calls"""
        try:
            existing_handles = self.db.get_all_handles()
            if existing_handles:
                # Add all existing handles to candidates_found and analyzed_handles
                self.candidates_found.update(existing_handles)
                self.analyzed_handles.update(existing_handles)
                logger.info(f"Loaded {len(existing_handles)} existing users from database (will skip these)")
        except Exception as e:
            logger.error(f"Error loading existing handles from database: {e}")

    def _save_progress(self):
        """Save current progress to file"""
        try:
            data = {
                'candidates_found': list(self.candidates_found),
                'processed_seeds': list(self.processed_seeds),
                'analyzed_handles': list(self.analyzed_handles),
                'last_updated': datetime.now(timezone.utc).isoformat()
            }
            with open(self.progress_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving progress: {e}")

    def _has_suspicious_username(self, handle: str) -> bool:
        """
        Check if username has patterns common in bots

        Indicators:
        - 8+ consecutive digits (e.g., user12345678)
        - Generic patterns like user123, account456
        """
        # Remove domain suffix for analysis
        username = handle.split('.')[0]

        # Check for 8+ consecutive digits
        if re.search(r'\d{8,}', username):
            return True

        # Check for very generic patterns
        generic_patterns = [
            r'^user\d{6,}$',
            r'^account\d{6,}$',
            r'^bot\d+$',
            r'^\w+\d{8,}$'
        ]

        for pattern in generic_patterns:
            if re.match(pattern, username, re.IGNORECASE):
                return True

        return False

    def _calculate_bot_probability(self, profile: BlueskyProfile) -> tuple[bool, float, List[str]]:
        """
        Calculate bot probability based on profile characteristics

        Returns:
            (is_bot_candidate, confidence_score, reasons)
        """
        reasons = []
        score = 0.0

        # Calculate metrics
        follow_ratio = (profile.follows_count / max(profile.followers_count, 1))
        has_profile_info = bool(profile.description or profile.avatar)

        # Calculate account age if available
        account_age_days = None
        if profile.created_at:
            account_age_days = (datetime.now(timezone.utc) - profile.created_at).days

        # HIGH PRIORITY INDICATORS (stronger signals)

        # Very high follow ratio + high following count
        if follow_ratio > 10 and profile.follows_count > 500:
            score += 0.4
            reasons.append(f"High follow ratio ({follow_ratio:.1f}:1) with {profile.follows_count} following")

        # New account with lots of posts
        if account_age_days and account_age_days < 30 and profile.posts_count > 500:
            score += 0.4
            reasons.append(f"New account ({account_age_days} days) with {profile.posts_count} posts")

        # Suspicious username
        if self._has_suspicious_username(profile.handle):
            score += 0.3
            reasons.append(f"Suspicious username pattern: {profile.handle}")

        # Very high posting rate (rough estimate)
        if account_age_days and account_age_days > 0:
            posts_per_day = profile.posts_count / account_age_days
            if posts_per_day > 150:
                score += 0.3
                reasons.append(f"Very high posting rate: {posts_per_day:.1f} posts/day")

        # No profile information
        if not has_profile_info:
            score += 0.2
            reasons.append("No bio or avatar")

        # MEDIUM PRIORITY INDICATORS

        # Moderately high follow ratio
        if 5 < follow_ratio <= 10 and profile.follows_count > 300:
            score += 0.2
            reasons.append(f"Elevated follow ratio ({follow_ratio:.1f}:1)")

        # Newer account with many posts
        if account_age_days and account_age_days < 90 and profile.posts_count > 2000:
            score += 0.2
            reasons.append(f"Relatively new ({account_age_days} days) with many posts ({profile.posts_count})")

        # Following suspiciously round numbers
        if profile.follows_count % 1000 == 0 and profile.follows_count > 0:
            score += 0.1
            reasons.append(f"Round number following count: {profile.follows_count}")

        # Zero followers on established account
        if profile.followers_count == 0 and profile.posts_count > 100:
            score += 0.3
            reasons.append("Zero followers despite many posts")

        # Determine if this is a bot candidate
        # Threshold: 0.5 or higher indicates bot-like behavior
        is_candidate = score >= 0.5

        return is_candidate, score, reasons

    async def analyze_account(self, handle: str) -> Optional[Dict]:
        """
        Analyze a single account for bot characteristics

        Returns:
            Account metadata dict if it's a bot candidate, None otherwise
        """
        # Skip if already analyzed in this session
        if handle in self.analyzed_handles:
            return None

        # Skip if already in database (avoid wasting API calls)
        existing_user = self.db.get_user(handle)
        if existing_user:
            logger.debug(f"Skipping {handle} - already in database")
            self.analyzed_handles.add(handle)
            # Add to candidates if it was previously stored
            self.candidates_found.add(handle)
            return None

        self.analyzed_handles.add(handle)

        try:
            # Fetch profile from Bluesky API (this costs an API call)
            profile = await self.client.get_profile(handle)
            if not profile:
                return None

            # Calculate bot probability
            is_candidate, score, reasons = self._calculate_bot_probability(profile)

            if is_candidate:
                logger.info(f"✓ Bot candidate: {handle} (score: {score:.2f})")
                for reason in reasons:
                    logger.info(f"  - {reason}")

                # Prepare metadata for database
                metadata = {
                    'description': profile.description or '',
                    'following': profile.follows_count,
                    'followers': profile.followers_count,
                    'ratio': profile.follows_count / max(profile.followers_count, 1),
                    'total_posts': profile.posts_count,
                    'replies_pct': 0.0,  # Will be calculated if we fetch posts
                    'reposts_pct': 0.0,
                    'originals_pct': 0.0
                }

                return metadata

            return None

        except Exception as e:
            logger.error(f"Error analyzing {handle}: {e}")
            return None

    async def process_seed_account(self, seed_handle: str, followers_limit: int = 100):
        """
        Process a seed account by analyzing its followers

        Args:
            seed_handle: The high-profile account to get followers from
            followers_limit: How many followers to fetch and analyze
        """
        if seed_handle in self.processed_seeds:
            logger.info(f"Skipping already processed seed: {seed_handle}")
            return

        logger.info(f"Processing seed account: {seed_handle}")

        try:
            # Get followers
            followers = await self.client.get_followers_sample(seed_handle, limit=followers_limit)
            logger.info(f"Got {len(followers)} followers from {seed_handle}")

            # Analyze each follower
            for i, follower_handle in enumerate(followers, 1):
                # Check if we've reached target
                if len(self.candidates_found) >= self.target_count:
                    logger.info(f"Target of {self.target_count} candidates reached!")
                    return

                # Skip if already a candidate
                if follower_handle in self.candidates_found:
                    continue

                # Analyze the follower
                metadata = await self.analyze_account(follower_handle)

                if metadata:
                    # Add to database
                    self.db.insert_user(follower_handle, metadata)
                    self.candidates_found.add(follower_handle)

                    logger.info(f"Progress: {len(self.candidates_found)}/{self.target_count} candidates found")

                # Rate limiting: small delay between requests
                if i % 10 == 0:
                    await asyncio.sleep(1)  # Brief pause every 10 accounts
                    self._save_progress()  # Save progress periodically

            # Mark seed as processed
            self.processed_seeds.add(seed_handle)
            self._save_progress()

        except Exception as e:
            logger.error(f"Error processing seed {seed_handle}: {e}")

    async def collect_candidates(self, seed_accounts: List[str]):
        """
        Main collection loop - process seed accounts until target is reached

        Args:
            seed_accounts: List of high-profile account handles to crawl
        """
        logger.info(f"Starting collection. Target: {self.target_count} candidates")
        logger.info(f"Starting with {len(self.candidates_found)} existing candidates")
        logger.info(f"Total seed accounts: {len(seed_accounts)}")

        for seed_handle in seed_accounts:
            if len(self.candidates_found) >= self.target_count:
                break

            await self.process_seed_account(seed_handle, followers_limit=100)

            # Save progress after each seed
            self._save_progress()

        logger.info(f"Collection complete! Found {len(self.candidates_found)} bot candidates")

        # Final progress save
        self._save_progress()


def load_seed_accounts(seed_file: str = "scripts/seed_accounts.json") -> List[str]:
    """Load seed accounts from JSON configuration file"""
    try:
        with open(seed_file, 'r') as f:
            data = json.load(f)

        # Flatten all categories into a single list
        all_seeds = []
        for category, handles in data.get('categories', {}).items():
            all_seeds.extend(handles)

        logger.info(f"Loaded {len(all_seeds)} seed accounts from {seed_file}")
        return all_seeds

    except Exception as e:
        logger.error(f"Error loading seed accounts: {e}")
        return []


async def main():
    """Main entry point"""
    import argparse
    from backend.config import Config

    parser = argparse.ArgumentParser(description='Collect bot candidate accounts from Bluesky')
    parser.add_argument('--target', type=int, default=1000, help='Target number of candidates to collect')
    parser.add_argument('--resume', action='store_true', help='Resume from previous progress')
    parser.add_argument('--seeds', type=str, default='scripts/seed_accounts.json', help='Path to seed accounts JSON file')

    args = parser.parse_args()

    # Load configuration (supports .env/config.json or environment variables)
    config = Config()

    if not config.has_bluesky_credentials():
        logger.error("Bluesky credentials not found in configuration")
        logger.error("Set them in .env/config.json or as environment variables:")
        logger.error("  export BLUESKY_USERNAME='your.handle.bsky.social'")
        logger.error("  export BLUESKY_PASSWORD='your-password'")
        sys.exit(1)

    bluesky_username = config.bluesky_username
    bluesky_password = config.bluesky_password

    # Initialize database
    db = BotDetectionDB("bot_detection.db")
    db.connect()
    db.initialize_schema()

    # Initialize Bluesky client
    async with BlueskyClient(bluesky_username, bluesky_password) as client:
        # Authenticate
        auth_success = await client.authenticate()
        if not auth_success:
            logger.error("Failed to authenticate with Bluesky")
            sys.exit(1)

        logger.info("Successfully authenticated with Bluesky")

        # Load seed accounts
        seed_accounts = load_seed_accounts(args.seeds)
        if not seed_accounts:
            logger.error("No seed accounts loaded. Check your seed accounts file.")
            sys.exit(1)

        # Create collector
        collector = BotCandidateCollector(
            db=db,
            client=client,
            target_count=args.target,
            progress_file="scripts/collection_progress.json"
        )

        # Start collection
        await collector.collect_candidates(seed_accounts)

    # Close database
    db.close()

    logger.info("Script completed successfully!")


if __name__ == "__main__":
    asyncio.run(main())
