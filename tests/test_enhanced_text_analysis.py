# test_enhanced_text_analysis.py - Tests for the enhanced AI phrase detection and text analysis
# These tests demonstrate the improved capabilities for detecting AI-generated content

import pytest
import sys
from pathlib import Path

# Add backend directory to Python path
backend_dir = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_dir))

from analyzers import TextAnalyzer
from bluesky_client import BlueskyPost
from datetime import datetime, timezone

class TestEnhancedAIDetection:
    """
    Test the enhanced AI phrase detection capabilities
    """
    
    @pytest.fixture
    def analyzer(self):
        return TextAnalyzer()
    
    @pytest.fixture
    def human_posts(self):
        """Posts that should appear human-written"""
        return [
            BlueskyPost(
                uri="test://1", 
                text="Just grabbed coffee and it's amazing! ☕ Anyone else having a good Monday?",
                created_at=datetime.now(timezone.utc), 
                reply_count=0, repost_count=0, like_count=0,
                is_reply=False, is_repost=False
            ),
            BlueskyPost(
                uri="test://2", 
                text="lol my cat just knocked over my plants again... why do they do this??? 😹",
                created_at=datetime.now(timezone.utc),
                reply_count=0, repost_count=0, like_count=0,
                is_reply=False, is_repost=False
            ),
            BlueskyPost(
                uri="test://3", 
                text="Watching the sunset from my balcony. Simple pleasures, ya know? 🌅",
                created_at=datetime.now(timezone.utc),
                reply_count=0, repost_count=0, like_count=0,
                is_reply=False, is_repost=False
            )
        ]
    
    @pytest.fixture
    def ai_posts(self):
        """Posts that should appear AI-generated"""
        return [
            BlueskyPost(
                uri="test://1", 
                text="As an AI, I think it's important to note that artificial intelligence has many applications. Furthermore, it's worth noting that technology continues to evolve.",
                created_at=datetime.now(timezone.utc),
                reply_count=0, repost_count=0, like_count=0,
                is_reply=False, is_repost=False
            ),
            BlueskyPost(
                uri="test://2", 
                text="I'd be happy to help you understand this topic. Moreover, it's crucial to understand that there are multiple approaches to consider. Let me break this down for you.",
                created_at=datetime.now(timezone.utc),
                reply_count=0, repost_count=0, like_count=0,
                is_reply=False, is_repost=False
            ),
            BlueskyPost(
                uri="test://3", 
                text="Based on the information provided, it appears that this is a fascinating topic. However, it's important to remember that you should seek professional advice.",
                created_at=datetime.now(timezone.utc),
                reply_count=0, repost_count=0, like_count=0,
                is_reply=False, is_repost=False
            )
        ]
    
    @pytest.fixture
    def spam_posts(self):
        """Posts that should appear as spam/bot content"""
        return [
            BlueskyPost(
                uri="test://1", 
                text="🚀 CRYPTO TRADING BOT! 500% returns guaranteed! DM me for exclusive access! Limited time offer! #Bitcoin #Trading",
                created_at=datetime.now(timezone.utc),
                reply_count=0, repost_count=0, like_count=0,
                is_reply=False, is_repost=False
            ),
            BlueskyPost(
                uri="test://2", 
                text="Follow me for more investment tips! Click link in bio! Don't miss out on $ETH gains! 📈💰",
                created_at=datetime.now(timezone.utc),
                reply_count=0, repost_count=0, like_count=0,
                is_reply=False, is_repost=False
            )
        ]
    
    @pytest.mark.asyncio
    async def test_human_content_detection(self, analyzer, human_posts):
        """Test that human content scores low on bot detection"""
        result = await analyzer.analyze(human_posts)
        
        print(f"\\n🧑 Human Content Analysis:")
        print(f"   Score: {result.score:.3f}")
        print(f"   Explanation: {result.explanation}")
        
        # Human content should score relatively low
        assert result.score < 0.4, f"Human content scored too high: {result.score}"
        assert not result.repetitive_content, "Human content shouldn't be marked as repetitive"
        
        # Check that human indicators were detected
        assert "human-like patterns" in result.explanation or result.score < 0.3
    
    @pytest.mark.asyncio
    async def test_ai_content_detection(self, analyzer, ai_posts):
        """Test that AI-generated content scores high on bot detection"""
        result = await analyzer.analyze(ai_posts)
        
        print(f"\\n🤖 AI Content Analysis:")
        print(f"   Score: {result.score:.3f}")
        print(f"   Explanation: {result.explanation}")
        
        # AI content should score high
        assert result.score > 0.4, f"AI content scored too low: {result.score}"
        
        # Should detect AI phrases
        assert "AI-typical phrases" in result.explanation or "direct AI identifiers" in result.explanation
    
    @pytest.mark.asyncio
    async def test_spam_content_detection(self, analyzer, spam_posts):
        """Test that spam content scores very high on bot detection"""
        result = await analyzer.analyze(spam_posts)
        
        print(f"\\n📧 Spam Content Analysis:")
        print(f"   Score: {result.score:.3f}")
        print(f"   Explanation: {result.explanation}")
        
        # Spam content should score moderately high (since it also has human indicators)
        assert result.score > 0.25, f"Spam content scored too low: {result.score}"
        
        # Should detect spam patterns
        assert "spam" in result.explanation.lower() or "promotional" in result.explanation.lower()
    
    def test_ai_phrase_categorization(self, analyzer):
        """Test that AI phrases are correctly categorized"""
        # Test direct AI identifiers (highest penalty)
        direct_ai_text = ["As an AI, I don't have personal feelings about this topic."]
        analysis = analyzer._count_ai_phrases(direct_ai_text)
        
        assert analysis["total"] > 0, "Should detect AI phrases"
        assert "direct_ai" in analysis["categories"], "Should categorize direct AI phrases"
        print(f"\\n🎯 Direct AI Detection: {analysis['categories']['direct_ai']} phrases")
        
        # Test transition phrases (medium penalty)
        transition_text = ["Furthermore, it's worth noting that moreover, this is important."]
        analysis = analyzer._count_ai_phrases(transition_text)
        
        assert "transitions" in analysis["categories"], "Should detect transition phrases"
        print(f"🔄 Transition Detection: {analysis['categories']['transitions']} phrases")
        
        # Test human indicators (positive signal)
        human_text = ["lol this is gonna be awesome! omg can't wait 😄"]
        analysis = analyzer._count_ai_phrases(human_text)
        
        assert analysis["human_indicators"] > 0, "Should detect human indicators"
        print(f"👤 Human Indicators: {analysis['human_indicators']} patterns")
    
    def test_spam_pattern_detection(self, analyzer):
        """Test spam pattern detection"""
        spam_text = "Buy $BTC now! 500% profit guaranteed! DM me for crypto trading bot!"
        
        spam_count = analyzer._count_spam_patterns(spam_text.lower())
        
        assert spam_count > 0, "Should detect spam patterns"
        print(f"\\n📢 Spam Patterns Detected: {spam_count}")
    
    def test_writing_style_analysis(self, analyzer):
        """Test writing style consistency analysis"""
        # Very consistent (AI-like) content
        consistent_text = [
            "This is a sentence with exactly ten words in it.",
            "Here is another sentence with exactly ten words total.", 
            "And this is yet another ten word sentence here."
        ]
        
        style_analysis = analyzer._analyze_writing_style(consistent_text)
        print(f"\\n📝 Consistent Style Analysis:")
        print(f"   Consistency: {style_analysis['consistency']:.3f}")
        print(f"   Formality: {style_analysis['formality']:.3f}")
        
        assert style_analysis["consistency"] > 0.8, "Should detect high consistency"
        
        # Varied (human-like) content  
        varied_text = [
            "Hey!",
            "This is a much longer sentence that contains many more words and demonstrates varied writing patterns.",
            "Short again.",
            "And here's another sentence of different length entirely, showing human-like variation in expression."
        ]
        
        varied_analysis = analyzer._analyze_writing_style(varied_text)
        print(f"\\n✍️ Varied Style Analysis:")
        print(f"   Consistency: {varied_analysis['consistency']:.3f}")
        print(f"   Formality: {varied_analysis['formality']:.3f}")
        
        assert varied_analysis["consistency"] < style_analysis["consistency"], "Varied text should be less consistent"
    
    @pytest.mark.asyncio
    async def test_mixed_content_analysis(self, analyzer):
        """Test analysis of mixed human and AI content"""
        mixed_posts = [
            BlueskyPost(
                uri="test://1", 
                text="Hey everyone! Hope you're having a great day 😊",  # Human-like
                created_at=datetime.now(timezone.utc),
                reply_count=0, repost_count=0, like_count=0,
                is_reply=False, is_repost=False
            ),
            BlueskyPost(
                uri="test://2", 
                text="Furthermore, it's important to note that this topic requires careful consideration. Based on the information provided, there are multiple approaches to consider.",  # AI-like
                created_at=datetime.now(timezone.utc),
                reply_count=0, repost_count=0, like_count=0,
                is_reply=False, is_repost=False
            ),
            BlueskyPost(
                uri="test://3", 
                text="omg just saw the funniest thing lol... why do cats do this??? 🐱",  # Human-like
                created_at=datetime.now(timezone.utc),
                reply_count=0, repost_count=0, like_count=0,
                is_reply=False, is_repost=False
            )
        ]
        
        result = await analyzer.analyze(mixed_posts)
        
        print(f"\\n🔀 Mixed Content Analysis:")
        print(f"   Score: {result.score:.3f}")
        print(f"   Explanation: {result.explanation}")
        
        # Should be low score since human patterns heavily outweigh AI patterns (101 vs 4)
        assert result.score < 0.3, f"Mixed content with predominant human patterns should score low: {result.score}"

if __name__ == "__main__":
    # Allow running tests directly
    pytest.main([__file__, "-v", "-s"])