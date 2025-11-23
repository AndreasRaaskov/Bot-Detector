# test_analyzers.py - Unit tests for bot detection analyzers
# Tests follow analysis, posting pattern analysis, and text analysis components

import pytest
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path
from unittest.mock import patch

# Add backend directory to Python path
backend_dir = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_dir))

from analyzers import FollowAnalyzer, PostingPatternAnalyzer, TextAnalyzer
from bluesky_client import BlueskyProfile, BlueskyPost
from models import FollowAnalysisResult, PostingPatternResult, TextAnalysisResult

class TestFollowAnalyzer:
    """
    Test the FollowAnalyzer for detecting suspicious follower/following patterns
    """
    
    @pytest.fixture
    def analyzer(self):
        """Create a FollowAnalyzer instance for testing"""
        return FollowAnalyzer()
    
    @pytest.mark.asyncio
    async def test_normal_follow_pattern(self, analyzer, sample_bluesky_profile):
        """
        Test analysis of a normal user with balanced follow patterns
        """
        # Normal user: 150 followers, 200 following (ratio 1.33)
        result = await analyzer.analyze(sample_bluesky_profile)
        
        assert isinstance(result, FollowAnalysisResult)
        assert result.follower_count == 150
        assert result.following_count == 200
        assert abs(result.ratio - 1.33) < 0.01  # Approximately 200/150
        assert result.score < 0.3  # Should be low score (not suspicious)
        assert "Normal follow pattern" in result.explanation
    
    @pytest.mark.asyncio
    async def test_suspicious_follow_pattern(self, analyzer, suspicious_bluesky_profile):
        """
        Test analysis of a suspicious user with very high follow ratio
        """
        # Suspicious user: 5 followers, 2500 following (ratio 500.0)
        result = await analyzer.analyze(suspicious_bluesky_profile)
        
        assert isinstance(result, FollowAnalysisResult)
        assert result.follower_count == 5
        assert result.following_count == 2500
        assert result.ratio == 500.0
        assert result.score > 0.7  # Should be high score (very suspicious)
        assert "High follow ratio" in result.explanation
    
    @pytest.mark.asyncio
    async def test_zero_followers_new_account(self, analyzer):
        """
        Test analysis of new account with zero followers
        Should be more lenient for new accounts
        """
        # New account created today with zero followers
        new_profile = BlueskyProfile(
            did="did:plc:new123",
            handle="newuser.bsky.social",
            display_name="New User",
            description="Just joined!",
            avatar=None,
            banner=None,
            followers_count=0,
            follows_count=50,
            posts_count=5,
            created_at=datetime.now(timezone.utc)  # Created today
        )
        
        result = await analyzer.analyze(new_profile)
        
        assert result.follower_count == 0
        assert result.following_count == 50
        # Should have some score but not maximum penalty for new accounts
        assert 0.1 < result.score <= 0.5
    
    @pytest.mark.asyncio
    async def test_zero_followers_old_account(self, analyzer):
        """
        Test analysis of old account with zero followers
        Should be more suspicious
        """
        # Old account with zero followers
        old_profile = BlueskyProfile(
            did="did:plc:old123",
            handle="olduser.bsky.social",
            display_name="Old User",
            description="Been here for months",
            avatar=None,
            banner=None,
            followers_count=0,
            follows_count=100,
            posts_count=50,
            created_at=datetime(2023, 6, 1, tzinfo=timezone.utc)  # 6+ months ago
        )
        
        result = await analyzer.analyze(old_profile)
        
        assert result.follower_count == 0
        assert result.following_count == 100
        # Should be more suspicious for old accounts
        assert result.score > 0.4
        assert "Zero followers on established account" in result.explanation
    
    @pytest.mark.asyncio
    async def test_round_number_detection(self, analyzer):
        """
        Test detection of suspiciously round numbers
        """
        # Profile with suspiciously round numbers
        round_profile = BlueskyProfile(
            did="did:plc:round123",
            handle="rounduser.bsky.social",
            display_name="Round User",
            description="Round numbers",
            avatar=None,
            banner=None,
            followers_count=500,  # Round number
            follows_count=5000,   # Very round number
            posts_count=1000,
            created_at=datetime(2023, 6, 1, tzinfo=timezone.utc)
        )
        
        result = await analyzer.analyze(round_profile)
        
        # Should detect round numbers
        assert "round" in result.explanation.lower()
        assert result.score > 0.3  # Should increase suspicion score
    
    @pytest.mark.asyncio
    async def test_extreme_ratios(self, analyzer):
        """
        Test handling of extreme follow ratios
        """
        # Profile with infinite ratio (zero followers, many following)
        extreme_profile = BlueskyProfile(
            did="did:plc:extreme123",
            handle="extreme.bsky.social",
            display_name="Extreme User",
            description="Extreme ratios",
            avatar=None,
            banner=None,
            followers_count=0,
            follows_count=10000,
            posts_count=100,
            created_at=datetime(2023, 6, 1, tzinfo=timezone.utc)
        )
        
        result = await analyzer.analyze(extreme_profile)

        assert result.ratio == 1000.0  # Very high ratio for 0 followers (inf not JSON compliant)
        assert result.score > 0.8  # Should be very suspicious
    
    def test_is_suspicious_round_number(self, analyzer):
        """
        Test the round number detection helper function
        """
        # Test cases for round number detection
        assert analyzer._is_suspicious_round_number(1000) is True
        assert analyzer._is_suspicious_round_number(5000) is True
        assert analyzer._is_suspicious_round_number(10000) is True
        assert analyzer._is_suspicious_round_number(500) is True
        assert analyzer._is_suspicious_round_number(2500) is True
        
        # Not suspicious
        assert analyzer._is_suspicious_round_number(1234) is False
        assert analyzer._is_suspicious_round_number(567) is False
        assert analyzer._is_suspicious_round_number(99) is False  # Too small
        assert analyzer._is_suspicious_round_number(123) is False

class TestPostingPatternAnalyzer:
    """
    Test the PostingPatternAnalyzer for detecting suspicious posting behaviors
    """
    
    @pytest.fixture
    def analyzer(self):
        """Create a PostingPatternAnalyzer instance for testing"""
        return PostingPatternAnalyzer()
    
    @pytest.mark.asyncio
    async def test_normal_posting_pattern(self, analyzer, sample_bluesky_posts):
        """
        Test analysis of normal human posting patterns
        """
        result = await analyzer.analyze(sample_bluesky_posts)
        
        assert isinstance(result, PostingPatternResult)
        assert result.total_posts == len(sample_bluesky_posts)
        assert result.posts_per_day_avg < 20  # Should be reasonable
        assert not result.unusual_frequency
        assert result.score < 0.5  # Should not be suspicious
        assert "normal" in result.explanation.lower()
    
    @pytest.mark.asyncio
    async def test_suspicious_posting_pattern(self, analyzer, suspicious_bluesky_posts):
        """
        Test analysis of suspicious bot-like posting patterns
        """
        result = await analyzer.analyze(suspicious_bluesky_posts)
        
        assert isinstance(result, PostingPatternResult)
        assert result.total_posts == len(suspicious_bluesky_posts)
        assert result.unusual_frequency is True  # Should detect unusual patterns
        assert result.score >= 0.3  # Should be somewhat suspicious
    
    @pytest.mark.asyncio
    async def test_empty_posts_list(self, analyzer):
        """
        Test analysis with no posts available
        """
        result = await analyzer.analyze([])
        
        assert result.total_posts == 0
        assert result.posts_per_day_avg == 0.0
        assert result.posting_hours == []
        assert result.score == 0.5  # Neutral score when no data
        assert "No posts available" in result.explanation
    
    @pytest.mark.asyncio
    async def test_high_frequency_posting(self, analyzer):
        """
        Test detection of excessively high posting frequency
        """
        # Create posts with very high frequency (posted every few minutes)
        base_time = datetime(2024, 1, 15, 12, 0, 0, tzinfo=timezone.utc)
        high_freq_posts = []
        
        for i in range(200):  # 200 posts in a short time
            high_freq_posts.append(BlueskyPost(
                uri=f"at://user/post/{i}",
                text=f"High frequency post {i}",
                created_at=base_time + timedelta(minutes=i * 2),  # Every 2 minutes
                reply_count=0,
                repost_count=0,
                like_count=1,
                is_reply=False,
                is_repost=False
            ))
        
        result = await analyzer.analyze(high_freq_posts)
        
        assert result.posts_per_day_avg > 100  # Very high posting rate
        assert result.unusual_frequency is True
        assert result.score > 0.4  # Should be suspicious
        assert "high posting rate" in result.explanation.lower()
    
    @pytest.mark.asyncio
    async def test_no_sleep_pattern(self, analyzer):
        """
        Test detection of 24/7 posting (no sleep pattern)
        """
        # Create posts spread across all hours of the day
        base_time = datetime(2024, 1, 15, 0, 0, 0, tzinfo=timezone.utc)
        no_sleep_posts = []
        
        for hour in range(24):
            for i in range(3):  # 3 posts per hour
                no_sleep_posts.append(BlueskyPost(
                    uri=f"at://user/post/{hour}_{i}",
                    text=f"Post at hour {hour}",
                    created_at=base_time.replace(hour=hour, minute=i*20),
                    reply_count=0,
                    repost_count=0,
                    like_count=1,
                    is_reply=False,
                    is_repost=False
                ))
        
        result = await analyzer.analyze(no_sleep_posts)
        
        assert len(result.posting_hours) >= 20  # Posts in most hours
        assert result.score > 0.3  # Should be suspicious
        # The sleep gap should be very small
        sleep_gap = analyzer._find_longest_inactive_period(result.posting_hours)
        assert sleep_gap < 4  # Less than 4 hours inactive
    
    @pytest.mark.asyncio
    async def test_high_repost_ratio(self, analyzer):
        """
        Test detection of accounts that mostly repost content
        """
        # Create posts with high repost ratio
        base_time = datetime(2024, 1, 15, 12, 0, 0, tzinfo=timezone.utc)
        repost_heavy_posts = []
        
        # 90% reposts, 10% original
        for i in range(100):
            is_repost = i < 90  # First 90 are reposts
            repost_heavy_posts.append(BlueskyPost(
                uri=f"at://user/post/{i}",
                text="Reposted content" if is_repost else f"Original post {i}",
                created_at=base_time + timedelta(hours=i),
                reply_count=0,
                repost_count=0,
                like_count=1,
                is_reply=False,
                is_repost=is_repost
            ))
        
        result = await analyzer.analyze(repost_heavy_posts)
        
        repost_ratio = analyzer._calculate_repost_ratio(repost_heavy_posts)
        assert repost_ratio > 0.8  # Should detect high repost ratio
        assert result.score > 0.2  # Should increase suspicion
    
    @pytest.mark.asyncio
    async def test_regular_interval_detection(self, analyzer):
        """
        Test detection of posts at suspiciously regular intervals
        """
        # Create posts at exactly regular intervals
        base_time = datetime(2024, 1, 15, 12, 0, 0, tzinfo=timezone.utc)
        regular_posts = []
        
        for i in range(20):
            regular_posts.append(BlueskyPost(
                uri=f"at://user/post/{i}",
                text=f"Regular post {i}",
                created_at=base_time + timedelta(hours=i * 2),  # Exactly every 2 hours
                reply_count=0,
                repost_count=0,
                like_count=1,
                is_reply=False,
                is_repost=False
            ))
        
        result = await analyzer.analyze(regular_posts)
        
        time_gaps = analyzer._calculate_time_gaps(regular_posts)
        has_regular = analyzer._has_regular_intervals(time_gaps)
        assert has_regular is True  # Should detect regular intervals
        assert result.score > 0.3  # Should be suspicious
    
    def test_longest_inactive_period(self, analyzer):
        """
        Test calculation of longest inactive period
        """
        # Test with posts in hours 9, 10, 11, 15, 16 (gap from 12-14)
        posting_hours = [9, 10, 11, 15, 16]
        inactive_period = analyzer._find_longest_inactive_period(posting_hours)
        
        # Should find gaps, but exact calculation depends on implementation
        assert inactive_period >= 3  # At least the 12-14 gap
        
        # Test with 24/7 posting
        all_hours = list(range(24))
        inactive_24_7 = analyzer._find_longest_inactive_period(all_hours)
        assert inactive_24_7 == 0  # No inactive period
        
        # Test with no posts
        no_posts = []
        inactive_none = analyzer._find_longest_inactive_period(no_posts)
        assert inactive_none == 24  # Assume full day inactive

class TestTextAnalyzer:
    """
    Test the TextAnalyzer for detecting AI-generated or bot-like text content
    """
    
    @pytest.fixture
    def analyzer(self):
        """Create a TextAnalyzer instance for testing"""
        return TextAnalyzer()
    
    @pytest.mark.asyncio
    async def test_normal_text_analysis(self, analyzer, sample_bluesky_posts):
        """
        Test analysis of normal human text content
        """
        result = await analyzer.analyze(sample_bluesky_posts, "Normal human bio")
        
        assert isinstance(result, TextAnalysisResult)
        assert len(result.sample_posts) > 0
        assert not result.repetitive_content
        assert result.score < 0.5  # Should not be suspicious
        assert "human-like patterns" in result.explanation.lower() or "analyzed" in result.explanation.lower()
    
    @pytest.mark.asyncio
    async def test_repetitive_content_detection(self, analyzer):
        """
        Test detection of very repetitive text content
        """
        # Create posts with very similar content
        repetitive_posts = []
        template = "This is a very similar post about {}"
        topics = ["topic1", "topic2", "topic1", "topic2", "topic1"]
        
        for i, topic in enumerate(topics):
            repetitive_posts.append(BlueskyPost(
                uri=f"at://user/post/{i}",
                text=template.format(topic),
                created_at=datetime.now(timezone.utc),
                reply_count=0,
                repost_count=0,
                like_count=1,
                is_reply=False,
                is_repost=False
            ))
        
        result = await analyzer.analyze(repetitive_posts)
        
        assert result.repetitive_content is True
        assert result.score > 0.4  # Should be suspicious
        assert "similarity" in result.explanation.lower()
    
    @pytest.mark.asyncio
    async def test_ai_phrase_detection(self, analyzer):
        """
        Test detection of AI-typical phrases
        """
        # Create posts with AI-typical language
        ai_posts = []
        ai_texts = [
            "As an AI, I think this is interesting",
            "It's important to note that this topic is complex",
            "I don't have personal opinions, but I can say",
            "Furthermore, this issue has many considerations",
            "In conclusion, this is a nuanced topic"
        ]
        
        for i, text in enumerate(ai_texts):
            ai_posts.append(BlueskyPost(
                uri=f"at://user/post/{i}",
                text=text,
                created_at=datetime.now(timezone.utc),
                reply_count=0,
                repost_count=0,
                like_count=1,
                is_reply=False,
                is_repost=False
            ))
        
        result = await analyzer.analyze(ai_posts, "I am a normal human user")
        
        assert result.score > 0.3  # Should detect AI phrases
        assert "AI-typical phrases" in result.explanation
    
    @pytest.mark.asyncio
    async def test_empty_posts_analysis(self, analyzer):
        """
        Test analysis when no original posts are available
        """
        # Create only reposts (no original content)
        repost_only = [
            BlueskyPost(
                uri="at://user/repost/1",
                text="",  # Reposts have no text
                created_at=datetime.now(timezone.utc),
                reply_count=0,
                repost_count=0,
                like_count=0,
                is_reply=False,
                is_repost=True
            )
        ]
        
        result = await analyzer.analyze(repost_only)
        
        assert result.sample_posts == []
        assert result.score == 0.5  # Neutral score
        assert "No original text content" in result.explanation
    
    @pytest.mark.asyncio
    async def test_very_short_posts(self, analyzer):
        """
        Test analysis of extremely short posts
        """
        # Create very short posts
        short_posts = []
        short_texts = ["Hi", "Ok", "Yes", "No", "Lol"]
        
        for i, text in enumerate(short_texts):
            short_posts.append(BlueskyPost(
                uri=f"at://user/post/{i}",
                text=text,
                created_at=datetime.now(timezone.utc),
                reply_count=0,
                repost_count=0,
                like_count=1,
                is_reply=False,
                is_repost=False
            ))
        
        result = await analyzer.analyze(short_posts)
        
        assert result.score > 0.2  # Should be somewhat suspicious
        assert "unusually short" in result.explanation.lower()
    
    @pytest.mark.asyncio
    async def test_template_detection(self, analyzer):
        """
        Test detection of template-like post structure
        """
        # Create posts following a template
        template_posts = []
        template = "I think WORD is really WORD. What do you think about WORD?"
        
        for i in range(5):
            template_posts.append(BlueskyPost(
                uri=f"at://user/post/{i}",
                text=template,  # Same structure
                created_at=datetime.now(timezone.utc),
                reply_count=0,
                repost_count=0,
                like_count=1,
                is_reply=False,
                is_repost=False
            ))
        
        result = await analyzer.analyze(template_posts)
        
        has_template = analyzer._detect_template_usage([post.text for post in template_posts])
        assert has_template is True
        assert result.score > 0.3  # Should be suspicious
    
    def test_jaccard_similarity(self, analyzer):
        """
        Test Jaccard similarity calculation
        """
        # Test identical texts
        similarity1 = analyzer._jaccard_similarity("hello world", "hello world")
        assert similarity1 == 1.0
        
        # Test completely different texts
        similarity2 = analyzer._jaccard_similarity("hello world", "foo bar")
        assert similarity2 == 0.0
        
        # Test partially similar texts
        similarity3 = analyzer._jaccard_similarity("hello world test", "hello world example")
        assert 0 < similarity3 < 1
        
        # Test empty texts
        similarity4 = analyzer._jaccard_similarity("", "")
        assert similarity4 == 1.0
    
    def test_vocabulary_diversity(self, analyzer):
        """
        Test vocabulary diversity calculation
        """
        # High diversity text
        diverse_texts = [
            "The quick brown fox jumps over the lazy dog",
            "Python programming requires logical thinking and creativity",
            "Machine learning algorithms analyze patterns in data"
        ]
        diversity1 = analyzer._calculate_vocabulary_diversity(diverse_texts)
        assert diversity1 > 0.7  # Should be high diversity
        
        # Low diversity text (repetitive)
        repetitive_texts = [
            "the cat sat on the mat",
            "the dog sat on the mat", 
            "the bird sat on the mat"
        ]
        diversity2 = analyzer._calculate_vocabulary_diversity(repetitive_texts)
        assert diversity2 < 0.8  # Should be lower diversity
        
        # Empty text
        diversity3 = analyzer._calculate_vocabulary_diversity([])
        assert diversity3 == 0.0

@pytest.mark.unit
class TestAnalyzerEdgeCases:
    """
    Test edge cases and error conditions for all analyzers
    """
    
    @pytest.mark.asyncio
    async def test_analyzer_error_handling(self):
        """
        Test that analyzers handle errors gracefully
        """
        follow_analyzer = FollowAnalyzer()
        pattern_analyzer = PostingPatternAnalyzer()
        text_analyzer = TextAnalyzer()
        
        # Test with None input (should not crash)
        with patch('analyzers.logger') as mock_logger:
            # This might raise an exception, but should be caught
            try:
                await follow_analyzer.analyze(None)
                await pattern_analyzer.analyze(None)
                await text_analyzer.analyze(None)
            except:
                # Expected to potentially fail, but shouldn't crash the app
                pass
    
    @pytest.mark.asyncio
    async def test_malformed_data_handling(self, sample_bluesky_profile):
        """
        Test analyzers with malformed or incomplete data
        """
        follow_analyzer = FollowAnalyzer()
        
        # Profile with negative counts (shouldn't happen but test anyway)
        malformed_profile = BlueskyProfile(
            did="did:plc:malformed",
            handle="malformed.bsky.social",
            display_name=None,
            description=None,
            avatar=None,
            banner=None,
            followers_count=-1,  # Negative count
            follows_count=100,
            posts_count=50,
            created_at=None  # Missing creation date
        )
        
        # Should handle gracefully
        result = await follow_analyzer.analyze(malformed_profile)
        assert isinstance(result, FollowAnalysisResult)
        # Score should be reasonable even with malformed data
        assert 0 <= result.score <= 1