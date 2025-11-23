#!/usr/bin/env python3
"""
Run bot detection analysis on all users in database
Uses the existing BotDetector to analyze all handles and store results
"""

import sys
import os
import asyncio
import logging

# Add backend to path (script is in project root)
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from backend.database import BotDetectionDB
from backend.bot_detector import BotDetector
from backend.config import Config

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def analyze_all_users(db_path: str = "bot_detection.db", batch_size: int = 10):
    """
    Run bot detection on all users in database

    Args:
        db_path: Path to database
        batch_size: Number of users to analyze before saving progress
    """
    # Initialize database
    db = BotDetectionDB(db_path)
    db.connect()

    # Get all handles
    handles = db.get_all_handles()
    total = len(handles)
    logger.info(f"Found {total} users to analyze")

    # Initialize bot detector with config
    # Config will look for .env/config.json or config.json
    project_root = os.path.dirname(__file__)

    # Look for .env/config.json (highest priority)
    env_config_path = os.path.join(project_root, '.env', 'config.json')

    # Initialize config with proper path to .env/config.json
    if os.path.exists(env_config_path):
        logger.info(f"Loading config from: {env_config_path}")
        config = Config(env_file_path=env_config_path)
    else:
        # Fall back to other config locations
        logger.info("No .env/config.json found, checking other locations...")
        config = Config()

    # Validate we have credentials
    if not config.has_bluesky_credentials():
        logger.error("No Bluesky credentials found!")
        logger.error("Please set up credentials in one of:")
        logger.error("  - .env/config.json in project root")
        logger.error("  - config.json in project root")
        logger.error("  - backend/config.json")
        logger.error("  - .env file with BLUESKY_USERNAME and BLUESKY_PASSWORD")
        logger.error("  - Environment variables")
        return

    detector = BotDetector(config)

    analyzed = 0
    errors = 0

    try:
        for idx, handle in enumerate(handles):
            logger.info(f"Analyzing {idx+1}/{total}: {handle}")

            try:
                # Run bot detection
                result = await detector.analyze_user(handle)

                # Store result in database
                db.insert_bot_detection_result(handle, {
                    'overall_score': result.overall_score,
                    'confidence': result.confidence,
                    'follow_analysis_score': result.follow_analysis.score,
                    'posting_pattern_score': result.posting_pattern.score,
                    'text_analysis_score': result.text_analysis.score,
                    'llm_analysis_score': result.llm_analysis.score,
                    'summary': result.summary,
                    'recommendations': ', '.join(result.recommendations)
                })

                analyzed += 1

                # Log progress
                if (idx + 1) % batch_size == 0:
                    logger.info(f"Progress: {analyzed} analyzed, {errors} errors")

            except Exception as e:
                logger.error(f"Error analyzing {handle}: {e}")
                errors += 1
                continue

    finally:
        # Cleanup
        await detector.close()
        db.close()

    logger.info(f"\nAnalysis complete!")
    logger.info(f"  Successfully analyzed: {analyzed}")
    logger.info(f"  Errors: {errors}")

if __name__ == "__main__":
    asyncio.run(analyze_all_users())
