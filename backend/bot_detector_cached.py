# bot_detector_cached.py - Database-cached bot detection
# This version checks the database first and only runs analysis if needed
# Skips LLM analysis to save costs and time

import asyncio
import time
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime

try:
    from .bluesky_client import BlueskyClient, BlueskyProfile, BlueskyPost
    from .analyzers import FollowAnalyzer, PostingPatternAnalyzer, TextAnalyzer
    from .models import (
        UserAnalysisResponse,
        FollowAnalysisResult,
        PostingPatternResult,
        TextAnalysisResult,
        LLMAnalysisResult
    )
    from .config import Config
    from .database import BotDetectionDB
except Exception:
    from bluesky_client import BlueskyClient, BlueskyProfile, BlueskyPost
    from analyzers import FollowAnalyzer, PostingPatternAnalyzer, TextAnalyzer
    from models import (
        UserAnalysisResponse,
        FollowAnalysisResult,
        PostingPatternResult,
        TextAnalysisResult,
        LLMAnalysisResult
    )
    from config import Config
    from database import BotDetectionDB

logger = logging.getLogger(__name__)


class CachedBotDetector:
    """
    Database-cached bot detector

    This version:
    1. Checks database for existing analysis
    2. Returns cached result if found
    3. Runs new analysis if not found
    4. Saves result to database
    5. Skips LLM analysis (too slow/expensive for every request)
    """

    def __init__(self, config: Optional[Config] = None, db_path: str = "bot_detection.db"):
        """
        Initialize the cached bot detector

        Args:
            config: Configuration object
            db_path: Path to SQLite database
        """
        self.config = config or Config()
        self.db = BotDetectionDB(db_path)
        self.db.connect()
        self.db.initialize_schema()

        # Initialize analysis components
        self.bluesky_client = None
        self.follow_analyzer = FollowAnalyzer()
        self.pattern_analyzer = PostingPatternAnalyzer()
        self.text_analyzer = TextAnalyzer()

        # Weights for combining scores (no LLM)
        self.weights = {
            "follow_analysis": 0.33,     # 33% weight
            "posting_pattern": 0.33,     # 33% weight
            "text_analysis": 0.34,       # 34% weight
        }

        logger.info("CachedBotDetector initialized with database caching")

    async def analyze_user(self, bluesky_handle: str, force_refresh: bool = False) -> UserAnalysisResponse:
        """
        Analyze user with database caching

        Args:
            bluesky_handle: Bluesky handle to analyze
            force_refresh: If True, ignore cache and run fresh analysis

        Returns:
            UserAnalysisResponse with analysis results
        """
        start_time = time.time()

        try:
            logger.info(f"Starting cached analysis for: {bluesky_handle}")

            # Step 1: Check database cache (unless force refresh)
            if not force_refresh:
                cached_result = self._load_from_database(bluesky_handle)
                if cached_result:
                    logger.info(f"Returning cached result for {bluesky_handle}")
                    return cached_result

            # Step 2: No cache found, run fresh analysis
            logger.info(f"No cache found, running fresh analysis for {bluesky_handle}")

            # Fetch user data
            profile, posts = await self._fetch_user_data(bluesky_handle)

            if not profile:
                return self._create_error_response(
                    bluesky_handle,
                    "User not found or unable to fetch profile data"
                )

            # Run analysis (without LLM)
            analysis_results = await self._run_analysis(profile, posts)

            # Calculate overall score
            overall_score, confidence = self._calculate_overall_score(analysis_results)

            # Generate assessment
            summary, recommendations = self._generate_assessment(
                overall_score, analysis_results, profile
            )

            # Calculate processing time
            processing_time_ms = int((time.time() - start_time) * 1000)

            # Create response
            response = UserAnalysisResponse(
                handle=profile.handle,
                display_name=profile.display_name,
                bio=profile.description,
                avatar_url=profile.avatar,
                created_at=profile.created_at,
                follow_analysis=analysis_results["follow_analysis"],
                posting_pattern=analysis_results["posting_pattern"],
                text_analysis=analysis_results["text_analysis"],
                llm_analysis=LLMAnalysisResult(
                    model_used="none",
                    score=None,
                    confidence=None,
                    reasoning="LLM analysis skipped in cached mode",
                    status="skipped",
                    error_code="LLM_DISABLED"
                ),
                overall_score=overall_score,
                confidence=confidence,
                summary=summary,
                recommendations=recommendations,
                processing_time_ms=processing_time_ms
            )

            # Step 3: Save to database
            self._save_to_database(profile, analysis_results, overall_score, confidence, summary, recommendations)

            logger.info(f"Analysis complete and cached for {bluesky_handle}: score={overall_score:.3f}")

            return response

        except Exception as e:
            logger.error(f"Analysis failed for {bluesky_handle}: {e}", exc_info=True)
            return self._create_error_response(
                bluesky_handle,
                f"Analysis failed: {str(e)}"
            )

    def _load_from_database(self, handle: str) -> Optional[UserAnalysisResponse]:
        """
        Load cached analysis from database

        Args:
            handle: Bluesky handle

        Returns:
            UserAnalysisResponse if found, None otherwise
        """
        try:
            # Get bot detection result
            result = self.db.get_bot_detection_result(handle)
            if not result:
                return None

            # Get user metadata
            user = self.db.get_user(handle)
            if not user:
                return None

            logger.debug(f"Found cached result for {handle} from {result.get('analyzed_at')}")

            # Reconstruct response from database
            return UserAnalysisResponse(
                handle=handle,
                display_name=handle,
                bio=user.get('description', ''),
                avatar_url='',
                created_at='',
                follow_analysis=FollowAnalysisResult(
                    score=result.get('follow_analysis_score', 0.0),
                    confidence=0.8,
                    ratio=user.get('ratio', 0.0),
                    followers=user.get('followers', 0),
                    following=user.get('following', 0),
                    assessment="cached"
                ),
                posting_pattern=PostingPatternResult(
                    score=result.get('posting_pattern_score', 0.0),
                    confidence=0.8,
                    regularity_score=0.0,
                    burst_score=0.0,
                    time_distribution_score=0.0,
                    assessment="cached"
                ),
                text_analysis=TextAnalysisResult(
                    score=result.get('text_analysis_score', 0.0),
                    confidence=0.8,
                    repetition_score=0.0,
                    diversity_score=0.0,
                    engagement_score=0.0,
                    assessment="cached"
                ),
                llm_analysis=LLMAnalysisResult(
                    model_used="cached",
                    score=None,
                    confidence=None,
                    reasoning="Loaded from database cache - LLM analysis was not performed",
                    status="cached",
                    error_code="LLM_DISABLED"
                ),
                overall_score=result.get('overall_score', 0.0),
                confidence=result.get('confidence', 0.0),
                summary=result.get('summary', 'Cached result'),
                recommendations=[result.get('recommendations', '')] if result.get('recommendations') else [],
                processing_time_ms=0  # Instant from cache
            )

        except Exception as e:
            logger.error(f"Failed to load from database for {handle}: {e}")
            return None

    def _save_to_database(self, profile: BlueskyProfile,
                         analysis_results: Dict[str, Any],
                         overall_score: float,
                         confidence: float,
                         summary: str,
                         recommendations: list[str]):
        """
        Save analysis results to database

        Args:
            profile: User profile
            analysis_results: Analysis results dict
            overall_score: Overall bot score
            confidence: Confidence level
            summary: Summary text
            recommendations: Recommendations text
        """
        try:
            # Save user metadata
            user_metadata = {
                'description': profile.description or '',
                'following': profile.following_count,
                'followers': profile.followers_count,
                'ratio': (profile.following_count / max(profile.followers_count, 1)),
                'total_posts': profile.posts_count,
            }
            self.db.insert_user(profile.handle, user_metadata)

            # Save bot detection result
            result_data = {
                'overall_score': overall_score,
                'confidence': confidence,
                'follow_analysis_score': analysis_results['follow_analysis'].score,
                'posting_pattern_score': analysis_results['posting_pattern'].score,
                'text_analysis_score': analysis_results['text_analysis'].score,
                'llm_analysis_score': 0.0,  # No LLM in cached mode
                'summary': summary,
                'recommendations': ', '.join(recommendations) if isinstance(recommendations, list) else recommendations
            }
            self.db.insert_bot_detection_result(profile.handle, result_data)

            logger.debug(f"Saved analysis to database for {profile.handle}")

        except Exception as e:
            logger.error(f"Failed to save to database: {e}")

    async def _fetch_user_data(self, handle: str) -> tuple[Optional[BlueskyProfile], List[BlueskyPost]]:
        """Fetch user profile and posts from Bluesky"""
        try:
            if not self.bluesky_client:
                self.bluesky_client = BlueskyClient(
                    username=self.config.bluesky_username,
                    password=self.config.bluesky_password
                )
                await self.bluesky_client.authenticate()

            profile = await self.bluesky_client.get_profile(handle)
            if not profile:
                return None, []

            posts = await self.bluesky_client.get_user_posts(handle, limit=100)

            logger.debug(f"Fetched profile and {len(posts)} posts for {handle}")
            return profile, posts

        except Exception as e:
            logger.error(f"Failed to fetch user data for {handle}: {e}")
            return None, []

    async def _run_analysis(self, profile: BlueskyProfile,
                           posts: List[BlueskyPost]) -> Dict[str, Any]:
        """Run analysis methods (without LLM)"""
        try:
            # Run analyzers in parallel (they're already async)
            results = await asyncio.gather(
                self.follow_analyzer.analyze(profile),
                self.pattern_analyzer.analyze(posts),
                self.text_analyzer.analyze(posts, profile.description),
                return_exceptions=True
            )

            # Extract results with defaults if error occurred
            follow_result = results[0] if not isinstance(results[0], Exception) else self._default_follow_result()
            pattern_result = results[1] if not isinstance(results[1], Exception) else self._default_pattern_result()
            text_result = results[2] if not isinstance(results[2], Exception) else self._default_text_result()

            return {
                "follow_analysis": follow_result,
                "posting_pattern": pattern_result,
                "text_analysis": text_result
            }

        except Exception as e:
            logger.error(f"Analysis failed: {e}")
            raise

    def _default_follow_result(self) -> FollowAnalysisResult:
        """Create default follow analysis result for errors"""
        return FollowAnalysisResult(
            follower_count=0,
            following_count=0,
            ratio=0.0,
            score=0.5,
            explanation="Analysis failed"
        )

    def _default_pattern_result(self) -> PostingPatternResult:
        """Create default posting pattern result for errors"""
        return PostingPatternResult(
            total_posts=0,
            posts_per_day_avg=0.0,
            posting_hours=[],
            unusual_frequency=False,
            score=0.5,
            explanation="Analysis failed"
        )

    def _default_text_result(self) -> TextAnalysisResult:
        """Create default text analysis result for errors"""
        return TextAnalysisResult(
            sample_posts=[],
            avg_perplexity=0.0,
            repetitive_content=False,
            score=0.5,
            explanation="Analysis failed"
        )

    def _calculate_overall_score(self, results: Dict[str, Any]) -> tuple[float, float]:
        """Calculate weighted overall score"""
        try:
            weighted_sum = 0.0
            total_weight = 0.0

            for key, weight in self.weights.items():
                if key in results and hasattr(results[key], 'score'):
                    weighted_sum += results[key].score * weight
                    total_weight += weight

            overall_score = weighted_sum / total_weight if total_weight > 0 else 0.5

            # Calculate confidence (average of individual confidences)
            confidences = [r.confidence for r in results.values() if hasattr(r, 'confidence')]
            confidence = sum(confidences) / len(confidences) if confidences else 0.5

            return overall_score, confidence

        except Exception as e:
            logger.error(f"Score calculation failed: {e}")
            return 0.5, 0.0

    def _generate_assessment(self, score: float, results: Dict[str, Any],
                           profile: BlueskyProfile) -> tuple[str, list[str]]:
        """Generate summary and recommendations"""
        summary = self._generate_summary(score)
        recommendations = self._generate_recommendations(score, results)
        return summary, recommendations

    def _generate_summary(self, score: float) -> str:
        """Generate summary text based on score"""
        if score >= 0.8:
            return "High likelihood of bot/automated account"
        elif score >= 0.6:
            return "Moderate likelihood of bot/automated account"
        elif score >= 0.4:
            return "Low likelihood of bot/automated account"
        else:
            return "Very low likelihood of bot/automated account - appears human"

    def _generate_recommendations(self, score: float, results: Dict[str, Any]) -> list[str]:
        """Generate recommendations"""
        if score < 0.4:
            return ["Account shows normal human behavior patterns."]
        elif score < 0.6:
            return ["Some suspicious patterns detected. Monitor for unusual activity."]
        else:
            return ["Multiple bot indicators detected. Exercise caution when engaging."]

    def _create_error_response(self, handle: str, error_msg: str) -> UserAnalysisResponse:
        """Create error response"""
        return UserAnalysisResponse(
            handle=handle,
            display_name="Error",
            bio="",
            avatar_url="",
            created_at="",
            follow_analysis=self._default_follow_result(),
            posting_pattern=self._default_pattern_result(),
            text_analysis=self._default_text_result(),
            llm_analysis=LLMAnalysisResult(
                model_used="error",
                score=None,
                confidence=None,
                reasoning=error_msg,
                status="failed",
                error_code="ANALYSIS_ERROR"
            ),
            overall_score=0.0,
            confidence=0.0,
            summary=error_msg,
            recommendations=[],
            processing_time_ms=0
        )

    def __del__(self):
        """Cleanup database connection"""
        try:
            if hasattr(self, 'db'):
                self.db.close()
        except:
            pass
