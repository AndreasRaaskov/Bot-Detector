# bot_detector.py - Main bot detection orchestrator
# This file combines all the different analyzers into a unified bot detection system
# It coordinates the analysis process and combines scores from different methods

import asyncio
import time
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime

try:
    from .bluesky_client import BlueskyClient, BlueskyProfile, BlueskyPost
    from .analyzers import FollowAnalyzer, PostingPatternAnalyzer, TextAnalyzer
    from .llm_analyzer import LLMAnalyzer
    from .models import (
        UserAnalysisResponse, 
        FollowAnalysisResult,
        PostingPatternResult, 
        TextAnalysisResult,
        LLMAnalysisResult
    )
    from .config import Config
except Exception:
    from bluesky_client import BlueskyClient, BlueskyProfile, BlueskyPost
    from analyzers import FollowAnalyzer, PostingPatternAnalyzer, TextAnalyzer
    from llm_analyzer import LLMAnalyzer
    from models import (
    UserAnalysisResponse, 
    FollowAnalysisResult,
    PostingPatternResult, 
    TextAnalysisResult,
    LLMAnalysisResult
    )
    from config import Config

logger = logging.getLogger(__name__)

class BotDetector:
    """
    Main bot detection system that orchestrates all analysis methods
    
    This class:
    1. Fetches user data from Bluesky
    2. Runs multiple analysis methods in parallel for efficiency
    3. Combines results into an overall bot score
    4. Provides detailed explanations and recommendations
    """
    
    def __init__(self, config: Optional[Config] = None):
        """
        Initialize the bot detector with configuration
        
        Args:
            config: Configuration object containing API keys and settings
                   If None, will try to load from environment/config files
        """
        self.config = config or Config()
        
        # Initialize the different analysis components
        self.bluesky_client = None  # Will be created when needed
        self.follow_analyzer = FollowAnalyzer()
        self.pattern_analyzer = PostingPatternAnalyzer()
        self.text_analyzer = TextAnalyzer()
        self.llm_analyzer = None  # Will be created when needed
        
        # Scoring weights for combining different analysis methods
        # These can be adjusted based on testing and feedback
        self.weights = {
            "follow_analysis": 0.25,     # 25% weight for follow patterns
            "posting_pattern": 0.25,     # 25% weight for posting timing
            "text_analysis": 0.25,       # 25% weight for text content analysis  
            "llm_analysis": 0.25         # 25% weight for LLM assessment
        }
        
        # Thresholds for overall bot classification
        self.bot_threshold_high = 0.8    # Score above this = very likely bot
        self.bot_threshold_medium = 0.6  # Score above this = possibly bot
        self.bot_threshold_low = 0.4     # Score below this = likely human
        
    async def analyze_user(self, bluesky_handle: str) -> UserAnalysisResponse:
        """
        Perform complete bot analysis on a Bluesky user
        
        Args:
            bluesky_handle: The Bluesky handle to analyze (e.g., "user.bsky.social")
            
        Returns:
            UserAnalysisResponse containing all analysis results and overall assessment
            
        This is the main entry point for bot detection analysis.
        """
        start_time = time.time()
        
        try:
            logger.info(f"Starting analysis for user: {bluesky_handle}")
            
            # Step 1: Fetch user data from Bluesky
            logger.debug("Fetching user data from Bluesky...")
            profile, posts = await self._fetch_user_data(bluesky_handle)
            
            if not profile:
                # If we can't find the user, return an error response
                return self._create_error_response(
                    bluesky_handle,
                    "User not found or unable to fetch profile data"
                )
            
            # Step 2: Run all analysis methods in parallel for efficiency
            logger.debug("Running parallel analysis...")
            analysis_results = await self._run_parallel_analysis(profile, posts)
            
            # Step 3: Combine results into overall score and assessment
            logger.debug("Combining analysis results...")
            overall_score, confidence = self._calculate_overall_score(analysis_results)
            
            # Step 4: Generate summary and recommendations
            summary, recommendations = self._generate_assessment(
                overall_score, analysis_results, profile
            )
            
            # Calculate processing time
            processing_time_ms = int((time.time() - start_time) * 1000)
            
            logger.info(f"Analysis complete for {bluesky_handle}: score={overall_score:.3f}, time={processing_time_ms}ms")
            
            # Step 5: Create and return the complete response
            return UserAnalysisResponse(
                handle=profile.handle,
                display_name=profile.display_name,
                bio=profile.description,
                avatar_url=profile.avatar,
                created_at=profile.created_at,
                follow_analysis=analysis_results["follow_analysis"],
                posting_pattern=analysis_results["posting_pattern"],
                text_analysis=analysis_results["text_analysis"],
                llm_analysis=analysis_results["llm_analysis"],
                overall_score=overall_score,
                confidence=confidence,
                summary=summary,
                recommendations=recommendations,
                processing_time_ms=processing_time_ms
            )
            
        except Exception as e:
            logger.error(f"Analysis failed for {bluesky_handle}: {e}")
            return self._create_error_response(
                bluesky_handle,
                f"Analysis failed: {str(e)}"
            )
    
    async def _fetch_user_data(self, handle: str) -> tuple[Optional[BlueskyProfile], List[BlueskyPost]]:
        """
        Fetch user profile and posts from Bluesky
        
        Args:
            handle: Bluesky handle to fetch data for
            
        Returns:
            Tuple of (profile, posts) or (None, []) if failed
        """
        try:
            # Create Bluesky client if not already created
            if not self.bluesky_client:
                self.bluesky_client = BlueskyClient(
                    username=self.config.bluesky_username,
                    password=self.config.bluesky_password
                )
                
                # Try to authenticate (this may fail if no credentials, but that's ok)
                await self.bluesky_client.authenticate()
            
            # Fetch user profile
            profile = await self.bluesky_client.get_profile(handle)
            if not profile:
                return None, []
            
            # Fetch recent posts for analysis
            posts = await self.bluesky_client.get_user_posts(handle, limit=100)
            
            logger.debug(f"Fetched profile and {len(posts)} posts for {handle}")
            return profile, posts
            
        except Exception as e:
            logger.error(f"Failed to fetch user data for {handle}: {e}")
            return None, []
    
    async def _run_parallel_analysis(self, profile: BlueskyProfile, 
                                   posts: List[BlueskyPost]) -> Dict[str, Any]:
        """
        Run all analysis methods in parallel for efficiency
        
        Args:
            profile: User profile data
            posts: List of user's posts
            
        Returns:
            Dictionary containing results from all analyzers
        """
        try:
            # Create all analysis tasks to run simultaneously
            tasks = []
            
            # Follow/follower analysis
            tasks.append(self.follow_analyzer.analyze(profile))
            
            # Posting pattern analysis
            tasks.append(self.pattern_analyzer.analyze(posts))
            
            # Text content analysis
            tasks.append(self.text_analyzer.analyze(posts, profile.description))
            
            # LLM analysis (create analyzer if needed)
            if not self.llm_analyzer and self.config.has_llm_keys():
                self.llm_analyzer = LLMAnalyzer(self.config.get_llm_keys())
            
            if self.llm_analyzer:
                # Extract post texts for LLM analysis
                post_texts = [post.text for post in posts if post.text and not post.is_repost]
                tasks.append(
                    self.llm_analyzer.analyze_content(
                        post_texts, 
                        profile.description or ""
                    )
                )
            else:
                # Create a placeholder LLM result if no LLM available
                tasks.append(self._create_placeholder_llm_result())
            
            # Run all analyses in parallel
            logger.debug("Running analyses in parallel...")
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Check for any exceptions and handle them
            follow_result = results[0] if not isinstance(results[0], Exception) else self._create_error_follow_result()
            pattern_result = results[1] if not isinstance(results[1], Exception) else self._create_error_pattern_result()
            text_result = results[2] if not isinstance(results[2], Exception) else self._create_error_text_result()
            llm_result = results[3] if not isinstance(results[3], Exception) else self._create_error_llm_result()
            
            return {
                "follow_analysis": follow_result,
                "posting_pattern": pattern_result,
                "text_analysis": text_result,
                "llm_analysis": llm_result
            }
            
        except Exception as e:
            logger.error(f"Parallel analysis failed: {e}")
            # Return error results for all analyzers
            return {
                "follow_analysis": self._create_error_follow_result(),
                "posting_pattern": self._create_error_pattern_result(),
                "text_analysis": self._create_error_text_result(),
                "llm_analysis": self._create_error_llm_result()
            }
    
    def _calculate_overall_score(self, analysis_results: Dict[str, Any]) -> tuple[float, float]:
        """
        Calculate overall bot score by combining individual analysis scores
        
        Args:
            analysis_results: Dictionary containing all analysis results
            
        Returns:
            Tuple of (overall_score, confidence)
            
        The overall score is a weighted average of individual scores.
        Confidence is based on how much data we had to work with.
        """
        try:
            # Extract individual scores
            follow_score = analysis_results["follow_analysis"].score
            pattern_score = analysis_results["posting_pattern"].score  
            text_score = analysis_results["text_analysis"].score
            llm_score = analysis_results["llm_analysis"].score
            
            # Calculate weighted average
            overall_score = (
                follow_score * self.weights["follow_analysis"] +
                pattern_score * self.weights["posting_pattern"] +
                text_score * self.weights["text_analysis"] +
                llm_score * self.weights["llm_analysis"]
            )
            
            # Calculate confidence based on data availability and consistency
            confidence = self._calculate_confidence(analysis_results)
            
            # Ensure score is between 0 and 1
            overall_score = max(0.0, min(1.0, overall_score))
            
            logger.debug(f"Overall score calculation: follow={follow_score:.3f}, pattern={pattern_score:.3f}, text={text_score:.3f}, llm={llm_score:.3f} -> overall={overall_score:.3f}")
            
            return overall_score, confidence
            
        except Exception as e:
            logger.error(f"Score calculation failed: {e}")
            return 0.5, 0.0  # Neutral score with zero confidence
    
    def _calculate_confidence(self, analysis_results: Dict[str, Any]) -> float:
        """
        Calculate confidence in our overall assessment
        
        Confidence is higher when:
        - We have more data to work with
        - Different analysis methods agree with each other
        - Individual analyzers report high confidence
        
        Args:
            analysis_results: Dictionary containing all analysis results
            
        Returns:
            Confidence score from 0.0 to 1.0
        """
        try:
            confidence_factors = []
            
            # Factor 1: Data availability
            total_posts = analysis_results["posting_pattern"].total_posts
            if total_posts >= 50:
                data_confidence = 1.0
            elif total_posts >= 20:
                data_confidence = 0.8
            elif total_posts >= 5:
                data_confidence = 0.6
            else:
                data_confidence = 0.3
            confidence_factors.append(data_confidence)
            
            # Factor 2: LLM confidence (if available)
            llm_confidence = analysis_results["llm_analysis"].confidence
            confidence_factors.append(llm_confidence)
            
            # Factor 3: Score consistency (how much do different methods agree?)
            scores = [
                analysis_results["follow_analysis"].score,
                analysis_results["posting_pattern"].score,
                analysis_results["text_analysis"].score,
                analysis_results["llm_analysis"].score
            ]
            
            # Calculate variance in scores (lower variance = higher confidence)
            if len(scores) > 1:
                mean_score = sum(scores) / len(scores)
                variance = sum((score - mean_score) ** 2 for score in scores) / len(scores)
                consistency_confidence = max(0.0, 1.0 - variance * 4)  # Scale variance to 0-1
                confidence_factors.append(consistency_confidence)
            
            # Combine confidence factors
            overall_confidence = sum(confidence_factors) / len(confidence_factors)
            return max(0.0, min(1.0, overall_confidence))
            
        except Exception as e:
            logger.warning(f"Confidence calculation failed: {e}")
            return 0.5
    
    def _generate_assessment(self, overall_score: float, analysis_results: Dict[str, Any], 
                           profile: BlueskyProfile) -> tuple[str, List[str]]:
        """
        Generate human-readable summary and recommendations
        
        Args:
            overall_score: The combined bot score
            analysis_results: Results from all analyzers
            profile: User profile information
            
        Returns:
            Tuple of (summary_text, recommendations_list)
        """
        try:
            # Generate overall assessment based on score thresholds
            if overall_score >= self.bot_threshold_high:
                assessment = "very likely a bot"
                risk_level = "HIGH"
            elif overall_score >= self.bot_threshold_medium:
                assessment = "possibly a bot"
                risk_level = "MEDIUM"
            elif overall_score <= self.bot_threshold_low:
                assessment = "likely human"
                risk_level = "LOW"
            else:
                assessment = "unclear - needs further investigation"
                risk_level = "MEDIUM"
            
            # Create summary
            summary = f"Analysis of @{profile.handle} indicates this account is {assessment} (risk level: {risk_level}, score: {overall_score:.2f}/1.00)."
            
            # Generate specific recommendations based on findings
            recommendations = []
            
            # Check each analysis method for significant findings
            if analysis_results["follow_analysis"].score >= 0.6:
                recommendations.append("⚠️ Suspicious follower/following patterns detected")
            
            if analysis_results["posting_pattern"].unusual_frequency:
                recommendations.append("⚠️ Unusual posting patterns detected")
            
            if analysis_results["text_analysis"].repetitive_content:
                recommendations.append("⚠️ Repetitive or template-like content detected")
            
            if analysis_results["llm_analysis"].score >= 0.6:
                recommendations.append("⚠️ Content appears AI-generated")
            
            # Add general recommendations based on overall score
            if overall_score >= self.bot_threshold_high:
                recommendations.extend([
                    "🚫 Consider blocking or reporting this account",
                    "📊 Multiple bot indicators detected across different analysis methods"
                ])
            elif overall_score >= self.bot_threshold_medium:
                recommendations.extend([
                    "👀 Monitor this account's future activity",
                    "🔍 Manual review recommended before taking action"
                ])
            else:
                recommendations.append("✅ Account appears to show normal human behavior patterns")
            
            # Add data quality notes
            post_count = analysis_results["posting_pattern"].total_posts
            if post_count < 10:
                recommendations.append("ℹ️ Limited post data available - analysis may be less reliable")
            
            return summary, recommendations
            
        except Exception as e:
            logger.error(f"Assessment generation failed: {e}")
            return "Analysis completed but assessment generation failed", ["Manual review recommended"]
    
    # Helper methods for creating error/placeholder results when analyses fail
    
    async def _create_placeholder_llm_result(self) -> LLMAnalysisResult:
        """Create a placeholder LLM result when no LLM is available"""
        return LLMAnalysisResult(
            model_used="none",
            confidence=0.0,
            reasoning="No LLM API keys configured",
            score=0.5
        )
    
    def _create_error_follow_result(self) -> FollowAnalysisResult:
        """Create error result for follow analysis"""
        return FollowAnalysisResult(
            follower_count=0,
            following_count=0,
            ratio=0.0,
            score=0.5,
            explanation="Follow analysis failed"
        )
    
    def _create_error_pattern_result(self) -> PostingPatternResult:
        """Create error result for posting pattern analysis"""
        return PostingPatternResult(
            total_posts=0,
            posts_per_day_avg=0.0,
            posting_hours=[],
            unusual_frequency=False,
            score=0.5,
            explanation="Posting pattern analysis failed"
        )
    
    def _create_error_text_result(self) -> TextAnalysisResult:
        """Create error result for text analysis"""
        return TextAnalysisResult(
            sample_posts=[],
            avg_perplexity=0.0,
            repetitive_content=False,
            score=0.5,
            explanation="Text analysis failed"
        )
    
    def _create_error_llm_result(self) -> LLMAnalysisResult:
        """Create error result for LLM analysis"""
        return LLMAnalysisResult(
            model_used="error",
            confidence=0.0,
            reasoning="LLM analysis failed",
            score=0.5
        )
    
    def _create_error_response(self, handle: str, error_message: str) -> UserAnalysisResponse:
        """Create an error response when analysis completely fails"""
        return UserAnalysisResponse(
            handle=handle,
            display_name=None,
            bio=None,
            avatar_url=None,
            created_at=None,
            follow_analysis=self._create_error_follow_result(),
            posting_pattern=self._create_error_pattern_result(),
            text_analysis=self._create_error_text_result(),
            llm_analysis=self._create_error_llm_result(),
            overall_score=0.5,
            confidence=0.0,
            summary=f"Analysis failed: {error_message}",
            recommendations=["Unable to analyze account", "Manual investigation required"],
            processing_time_ms=0
        )
    
    async def close(self):
        """
        Clean up resources when done with the bot detector
        Call this when shutting down the application
        """
        if self.bluesky_client:
            await self.bluesky_client.close()
        
        if self.llm_analyzer:
            await self.llm_analyzer.close()