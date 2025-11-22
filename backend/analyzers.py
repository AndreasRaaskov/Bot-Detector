# analyzers.py - Bot detection analysis modules
# This file contains different analysis methods for detecting bot behavior
# Each analyzer focuses on a specific aspect of bot detection

import re
import math
import statistics
from typing import List, Dict, Set, Tuple, Optional
from datetime import datetime, timedelta
from collections import Counter, defaultdict
import logging

try:
    from .bluesky_client import BlueskyProfile, BlueskyPost
    from .models import (
        FollowAnalysisResult,
        PostingPatternResult,
        TextAnalysisResult
    )
except Exception:
    from bluesky_client import BlueskyProfile, BlueskyPost
    from models import (
        FollowAnalysisResult,
        PostingPatternResult,
        TextAnalysisResult
    )

logger = logging.getLogger(__name__)

class FollowAnalyzer:
    """
    Analyzes follower/following ratios to detect suspicious accounts
    
    Bot indicators:
    - High following count with very few followers (follow-spraying)
    - Perfectly round numbers (suggesting batch operations)
    - Extreme ratios that are unusual for human behavior
    """
    
    def __init__(self):
        # These thresholds are based on research from the brainstorm document
        # They can be adjusted based on testing and feedback
        self.suspicious_ratio_threshold = 5.0  # Following:follower ratio above this is suspicious
        self.high_follow_threshold = 1000  # Following more than this is suspicious
        self.new_account_days = 30  # Accounts newer than this get different scoring
    
    async def analyze(self, profile: BlueskyProfile) -> FollowAnalysisResult:
        """
        Analyze a user's follower/following patterns
        
        Args:
            profile: BlueskyProfile containing follower/following counts
            
        Returns:
            FollowAnalysisResult with scoring and explanation
        """
        try:
            followers = profile.followers_count
            following = profile.follows_count
            
            # Calculate the ratio (avoid division by zero)
            if followers == 0:
                # If no followers but following people, this is very suspicious
                ratio = float('inf') if following > 0 else 0
            else:
                ratio = following / followers
            
            # Start building our bot score (0 = human-like, 1 = bot-like)
            score = 0.0
            red_flags = []
            
            # Check for high ratio (following many, followed by few)
            if ratio > self.suspicious_ratio_threshold:
                score += 0.4  # Major red flag
                red_flags.append(f"High follow ratio ({ratio:.1f}:1)")
            elif ratio > 2.0:
                score += 0.2  # Moderate concern
                red_flags.append(f"Elevated follow ratio ({ratio:.1f}:1)")
            
            # Check for excessive following count
            if following > self.high_follow_threshold:
                score += 0.3
                red_flags.append(f"Following {following:,} accounts (very high)")
            elif following > 500:
                score += 0.1
                red_flags.append(f"Following {following:,} accounts (high)")
            
            # Check for round numbers (might indicate automation)
            if self._is_suspicious_round_number(following):
                score += 0.1
                red_flags.append("Following count is suspiciously round")
            
            if self._is_suspicious_round_number(followers):
                score += 0.05
                red_flags.append("Follower count is suspiciously round")
            
            # Check for zero followers (new accounts get some leniency)
            if followers == 0:
                account_age = self._get_account_age_days(profile.created_at)
                if account_age is None or account_age > self.new_account_days:
                    score += 0.2
                    red_flags.append("Zero followers on established account")
                elif following > 0:
                    score += 0.1
                    red_flags.append("Zero followers but actively following")
            
            # Cap the score at 1.0
            score = min(score, 1.0)
            
            # Generate explanation
            explanation = self._generate_explanation(
                followers, following, ratio, red_flags
            )
            
            return FollowAnalysisResult(
                follower_count=followers,
                following_count=following,
                ratio=ratio,
                score=score,
                explanation=explanation
            )
            
        except Exception as e:
            logger.error(f"Follow analysis error: {e}")
            # Return a neutral result if analysis fails
            return FollowAnalysisResult(
                follower_count=0,
                following_count=0,
                ratio=0.0,
                score=0.5,  # Neutral score when we can't analyze
                explanation="Analysis failed - unable to assess follow patterns"
            )
    
    def _is_suspicious_round_number(self, count: int) -> bool:
        """
        Check if a number is suspiciously round (might indicate automation)
        
        Args:
            count: The count to check
            
        Returns:
            True if the number seems artificially round
        """
        if count < 100:
            return False  # Small numbers are often round naturally
        
        # Check for numbers like 1000, 5000, 10000, etc.
        if count % 1000 == 0 and count >= 1000:
            return True
        
        # Check for numbers like 500, 2500, etc.
        if count % 500 == 0 and count >= 500:
            return True
        
        return False
    
    def _get_account_age_days(self, created_at: Optional[datetime]) -> Optional[int]:
        """
        Calculate how old an account is in days
        
        Args:
            created_at: When the account was created
            
        Returns:
            Age in days, or None if creation date unknown
        """
        if not created_at:
            return None
        
        try:
            now = datetime.now(created_at.tzinfo)
            age = now - created_at
            return age.days
        except Exception:
            return None
    
    def _generate_explanation(self, followers: int, following: int, 
                            ratio: float, red_flags: List[str]) -> str:
        """
        Generate a human-readable explanation of the analysis
        
        Args:
            followers: Follower count
            following: Following count  
            ratio: Following/follower ratio
            red_flags: List of identified issues
            
        Returns:
            Human-readable explanation string
        """
        if not red_flags:
            return f"Normal follow pattern: {following:,} following, {followers:,} followers"
        
        explanation = f"Account follows {following:,} and has {followers:,} followers (ratio {ratio:.1f}:1). "
        
        if len(red_flags) == 1:
            explanation += f"Concern: {red_flags[0]}."
        else:
            explanation += f"Concerns: {', '.join(red_flags[:-1])}, and {red_flags[-1]}."
        
        return explanation


class PostingPatternAnalyzer:
    """
    Analyzes posting patterns to detect bot-like behavior
    
    Bot indicators:
    - Posting at inhuman frequencies (too fast or too consistent)
    - Posting at unusual times (never sleeping)
    - Perfectly regular intervals between posts
    - Very high repost-to-original ratio
    """
    
    def __init__(self):
        # These thresholds are based on typical human behavior patterns
        self.max_human_posts_per_hour = 20  # Posting more than this per hour is suspicious
        self.max_human_posts_per_day = 100  # Posting more than this per day is suspicious
        self.min_sleep_hours = 4  # Humans typically don't post for at least 4 consecutive hours
        self.high_repost_ratio = 0.8  # If >80% of posts are reposts, it's suspicious
    
    async def analyze(self, posts: List[BlueskyPost]) -> PostingPatternResult:
        """
        Analyze posting patterns from a user's recent posts
        
        Args:
            posts: List of BlueskyPost objects to analyze
            
        Returns:
            PostingPatternResult with scoring and explanation
        """
        try:
            if not posts:
                return PostingPatternResult(
                    total_posts=0,
                    posts_per_day_avg=0.0,
                    posting_hours=[],
                    unusual_frequency=False,
                    score=0.5,  # Neutral score - can't analyze without posts
                    explanation="No posts available for pattern analysis"
                )
            
            # Calculate basic statistics
            total_posts = len(posts)
            posting_hours = self._extract_posting_hours(posts)
            posts_per_day = self._calculate_posts_per_day(posts)
            time_gaps = self._calculate_time_gaps(posts)
            repost_ratio = self._calculate_repost_ratio(posts)
            
            # Analyze for bot-like patterns
            score = 0.0
            red_flags = []
            
            # Check posting frequency
            if posts_per_day > self.max_human_posts_per_day:
                score += 0.4
                red_flags.append(f"Very high posting rate ({posts_per_day:.1f} posts/day)")
            elif posts_per_day > 50:
                score += 0.2
                red_flags.append(f"High posting rate ({posts_per_day:.1f} posts/day)")
            
            # Check for inhuman posting hours (no sleep pattern)
            sleep_gap = self._find_longest_inactive_period(posting_hours)
            if sleep_gap < self.min_sleep_hours:
                score += 0.3
                red_flags.append(f"No clear sleep pattern (max {sleep_gap}h inactive)")
            
            # Check for suspiciously regular intervals
            if self._has_regular_intervals(time_gaps):
                score += 0.3
                red_flags.append("Posts at suspiciously regular intervals")
            
            # Check for very high repost ratio
            if repost_ratio > self.high_repost_ratio:
                score += 0.2
                red_flags.append(f"Very high repost ratio ({repost_ratio:.1%})")
            
            # Check for burst posting (many posts in short time)
            if self._detect_burst_posting(posts):
                score += 0.2
                red_flags.append("Detected burst posting behavior")
            
            # Cap score at 1.0
            score = min(score, 1.0)
            
            explanation = self._generate_pattern_explanation(
                total_posts, posts_per_day, posting_hours, red_flags
            )
            
            return PostingPatternResult(
                total_posts=total_posts,
                posts_per_day_avg=posts_per_day,
                posting_hours=sorted(set(posting_hours)),
                unusual_frequency=len(red_flags) > 0,
                score=score,
                explanation=explanation
            )
            
        except Exception as e:
            logger.error(f"Posting pattern analysis error: {e}")
            return PostingPatternResult(
                total_posts=0,
                posts_per_day_avg=0.0,
                posting_hours=[],
                unusual_frequency=False,
                score=0.5,
                explanation="Analysis failed - unable to assess posting patterns"
            )
    
    def _extract_posting_hours(self, posts: List[BlueskyPost]) -> List[int]:
        """Extract the hours (0-23) when posts were made"""
        hours = []
        for post in posts:
            if post.created_at:
                hours.append(post.created_at.hour)
        return hours
    
    def _calculate_posts_per_day(self, posts: List[BlueskyPost]) -> float:
        """Calculate average posts per day"""
        if not posts:
            return 0.0
        
        # Find the date range of posts
        dates = [post.created_at for post in posts if post.created_at]
        if not dates:
            return 0.0
        
        min_date = min(dates)
        max_date = max(dates)
        
        # Calculate days between first and last post
        days = (max_date - min_date).days + 1  # +1 to include both start and end days
        
        return len(posts) / max(days, 1)  # Avoid division by zero
    
    def _calculate_time_gaps(self, posts: List[BlueskyPost]) -> List[float]:
        """Calculate time gaps between consecutive posts in hours"""
        gaps = []
        sorted_posts = sorted([p for p in posts if p.created_at], 
                            key=lambda x: x.created_at)
        
        for i in range(1, len(sorted_posts)):
            gap = sorted_posts[i].created_at - sorted_posts[i-1].created_at
            gaps.append(gap.total_seconds() / 3600)  # Convert to hours
        
        return gaps
    
    def _calculate_repost_ratio(self, posts: List[BlueskyPost]) -> float:
        """Calculate what fraction of posts are reposts"""
        if not posts:
            return 0.0
        
        reposts = sum(1 for post in posts if post.is_repost)
        return reposts / len(posts)
    
    def _find_longest_inactive_period(self, posting_hours: List[int]) -> int:
        """Find the longest consecutive period with no posts (in hours)"""
        if not posting_hours:
            return 24  # If no posts, assume 24-hour inactive period
        
        # Count posts in each hour of the day
        hour_counts = Counter(posting_hours)
        
        # Find longest consecutive period of hours with zero posts
        max_inactive = 0
        current_inactive = 0
        
        # Check each hour of the day (0-23, then wrap around)
        for hour in list(range(24)) * 2:  # Double to handle wrap-around
            if hour_counts.get(hour % 24, 0) == 0:
                current_inactive += 1
                max_inactive = max(max_inactive, current_inactive)
            else:
                current_inactive = 0
                
        return min(max_inactive, 24)  # Cap at 24 hours
    
    def _has_regular_intervals(self, time_gaps: List[float]) -> bool:
        """Check if posts are made at suspiciously regular intervals"""
        if len(time_gaps) < 5:  # Need enough data points
            return False
        
        # Calculate standard deviation of time gaps
        if len(time_gaps) >= 2:
            mean_gap = statistics.mean(time_gaps)
            if mean_gap > 0:
                std_dev = statistics.stdev(time_gaps)
                coefficient_of_variation = std_dev / mean_gap
                
                # If variation is very low, intervals are suspiciously regular
                return coefficient_of_variation < 0.1
        
        return False
    
    def _detect_burst_posting(self, posts: List[BlueskyPost]) -> bool:
        """Detect if user posts many times in short bursts"""
        if len(posts) < 10:
            return False
        
        # Group posts by hour and count
        hour_groups = defaultdict(int)
        for post in posts:
            if post.created_at:
                hour_key = post.created_at.replace(minute=0, second=0, microsecond=0)
                hour_groups[hour_key] += 1
        
        # Check if any hour has an unusually high number of posts
        hour_counts = list(hour_groups.values())
        if hour_counts:
            max_posts_per_hour = max(hour_counts)
            return max_posts_per_hour > self.max_human_posts_per_hour
        
        return False
    
    def _generate_pattern_explanation(self, total_posts: int, posts_per_day: float,
                                    posting_hours: List[int], red_flags: List[str]) -> str:
        """Generate human-readable explanation of posting pattern analysis"""
        
        explanation = f"Analyzed {total_posts} posts averaging {posts_per_day:.1f} posts per day. "
        
        if posting_hours:
            hour_range = f"{min(posting_hours)}:00-{max(posting_hours)}:00"
            explanation += f"Posts during hours {hour_range}. "
        
        if not red_flags:
            explanation += "Posting patterns appear normal for human behavior."
        else:
            explanation += f"Concerns: {', '.join(red_flags)}."
        
        return explanation


class TextAnalyzer:
    """
    Analyzes text content to detect AI-generated or bot-like content
    
    Bot indicators:
    - Repetitive phrases or templates
    - Unusual vocabulary patterns
    - Extremely consistent writing style
    - Generic or meaningless content
    """
    
    def __init__(self):
        # Expanded AI-typical phrases and patterns
        self.ai_phrases = {
            # Direct AI identifiers
            "direct_ai": [
                "as an ai", "i'm an ai", "artificial intelligence", "large language model",
                "i don't have personal", "i don't have feelings", "i don't have emotions",
                "i cannot", "i'm not able to", "i don't have the ability to",
                "i don't have access to", "i can't browse the internet", "i don't have real-time",
                "as a language model", "as an artificial intelligence"
            ],
            
            # Formal/academic transition phrases (overused by AI)
            "transitions": [
                "it's worth noting", "it's important to note", "it's crucial to understand",
                "furthermore", "moreover", "additionally", "consequently", "nonetheless",
                "in conclusion", "in summary", "to summarize", "that being said",
                "on the other hand", "however", "nevertheless", "it should be noted"
            ],
            
            # AI hedging language (uncertainty markers)
            "hedging": [
                "it seems like", "it appears that", "it looks like", "it might be",
                "potentially", "possibly", "presumably", "allegedly", "reportedly",
                "it's likely that", "there's a possibility", "it could be argued",
                "some might say", "one could argue", "it's reasonable to assume"
            ],
            
            # Overly helpful/formal language
            "helpful": [
                "i'd be happy to help", "i'm here to assist", "feel free to ask",
                "please don't hesitate", "i hope this helps", "let me know if you need",
                "is there anything else", "happy to clarify", "please let me know"
            ],
            
            # Generic positive statements (AI tends to be overly positive)
            "generic_positive": [
                "that's a great question", "excellent point", "wonderful idea",
                "fantastic", "absolutely", "definitely agree", "great observation",
                "very interesting", "fascinating topic", "excellent choice"
            ],
            
            # AI safety/disclaimer language
            "disclaimers": [
                "please note that", "it's important to remember", "keep in mind",
                "please be aware", "it's worth mentioning", "i should mention",
                "please consult", "seek professional advice", "i recommend consulting"
            ],
            
            # ChatGPT/Claude specific patterns
            "chatgpt_patterns": [
                "i understand you're asking", "to answer your question", "based on the information provided",
                "here's what i can tell you", "let me break this down", "here's a breakdown",
                "there are several factors", "multiple approaches", "various ways to",
                "it depends on several factors", "there are pros and cons"
            ]
        }
        
        # Flatten all phrases for easy searching
        self.all_ai_phrases = []
        for category in self.ai_phrases.values():
            self.all_ai_phrases.extend(category)
        
        # Threshold for text similarity (how similar posts can be before it's suspicious)
        self.similarity_threshold = 0.8
        
        # Common bot/spam patterns
        self.spam_patterns = [
            r'\b(?:crypto|nft|bitcoin|ethereum|trading|investment)\b',
            r'\b(?:follow\s+me|click\s+link|check\s+out)\b',
            r'\b(?:dm\s+me|message\s+me|contact\s+me)\b',
            r'\$[A-Z]{3,5}\b',  # Crypto ticker symbols
            r'\b\d+%\s+(?:profit|return|gain)\b',  # Investment returns
            r'\b(?:limited\s+time|act\s+now|don\'t\s+miss)\b'  # Urgency language
        ]
        
        # Patterns that suggest human authenticity
        self.human_indicators = [
            r'\b(?:lol|haha|omg|wtf|brb|imo|imho)\b',  # Informal abbreviations
            r'[.]{2,}|[!]{2,}|[?]{2,}',  # Multiple punctuation
            r'\b(?:gonna|wanna|gotta|kinda|sorta)\b',  # Contractions
            r'[a-z][A-Z]',  # Mixed case (typos)
            r'\b(?:um|uh|hmm|meh|nah|yep|yup)\b',  # Hesitation/informal responses
            r'[😀-🙏]',  # Emoji patterns
            r'\b(?:dude|buddy|mate|bro|sis)\b',  # Casual address terms
        ]
        
    async def analyze(self, posts: List[BlueskyPost], 
                     profile_text: Optional[str] = None) -> TextAnalysisResult:
        """
        Analyze text content for bot-like patterns
        
        Args:
            posts: List of posts to analyze
            profile_text: User's bio/description text
            
        Returns:
            TextAnalysisResult with analysis results
        """
        try:
            # Filter to only original posts (not reposts/replies)
            original_posts = [p for p in posts if not p.is_repost and p.text.strip()]
            
            if not original_posts:
                return TextAnalysisResult(
                    sample_posts=[],
                    avg_perplexity=0.0,
                    repetitive_content=False,
                    score=0.5,  # Neutral - can't analyze without content
                    explanation="No original text content available for analysis"
                )
            
            # Collect all text for analysis
            post_texts = [post.text for post in original_posts]
            sample_posts = post_texts[:10]  # Keep a sample for the response
            
            score = 0.0
            red_flags = []
            
            # Check for repetitive content
            similarity_score = self._calculate_text_similarity(post_texts)
            if similarity_score > self.similarity_threshold:
                score += 0.4
                red_flags.append(f"High text similarity between posts ({similarity_score:.1%})")
            
            # Enhanced AI phrase detection
            ai_analysis = self._count_ai_phrases(post_texts + ([profile_text] if profile_text else []))
            ai_phrase_count = ai_analysis["total"]
            
            if ai_phrase_count > 0:
                # Weight different types of AI phrases differently
                direct_ai_count = ai_analysis["categories"].get("direct_ai", 0)
                if direct_ai_count > 0:
                    score += 0.5  # High penalty for direct AI identifiers
                    red_flags.append(f"Contains {direct_ai_count} direct AI identifiers")
                
                other_ai_count = ai_phrase_count - direct_ai_count
                if other_ai_count > 0:
                    score += min(other_ai_count * 0.05, 0.3)  # Gradual penalty for other AI phrases
                    red_flags.append(f"Contains {other_ai_count} AI-typical phrases")
            
            # Check for spam patterns
            spam_count = ai_analysis.get("spam_patterns", 0)
            if spam_count > 0:
                score += min(spam_count * 0.1, 0.3)
                red_flags.append(f"Contains {spam_count} spam/promotional patterns")
            
            # Factor in human indicators (positive signal)
            human_indicators = ai_analysis.get("human_indicators", 0)
            if human_indicators > 0:
                score -= min(human_indicators * 0.05, 0.2)  # Reduce score for human indicators
                red_flags.append(f"✅ Contains {human_indicators} human-like patterns")
            
            # Check for extremely short or generic content
            avg_length = statistics.mean([len(text.split()) for text in post_texts])
            if avg_length < 3:  # Very short posts
                score += 0.2
                red_flags.append("Posts are unusually short")
            
            # Check for template-like structure
            if self._detect_template_usage(post_texts):
                score += 0.3
                red_flags.append("Posts follow template-like patterns")
            
            # Analyze writing style patterns
            style_analysis = self._analyze_writing_style(post_texts)
            
            # High consistency in writing style suggests AI
            if style_analysis["consistency"] > 0.8:
                score += 0.2
                red_flags.append(f"Very consistent writing style (consistency: {style_analysis['consistency']:.2f})")
            
            # Very high formality might suggest AI
            if style_analysis["formality"] > 0.7:
                score += 0.15
                red_flags.append(f"Overly formal language (formality: {style_analysis['formality']:.2f})")
            
            # Check vocabulary diversity
            vocab_diversity = self._calculate_vocabulary_diversity(post_texts)
            if vocab_diversity < 0.3:  # Low diversity indicates repetitive language
                score += 0.2
                red_flags.append(f"Low vocabulary diversity ({vocab_diversity:.2f})")
            elif vocab_diversity > 0.7:  # High diversity suggests human creativity
                score -= 0.1
                red_flags.append(f"✅ High vocabulary diversity ({vocab_diversity:.2f})")
            
            # Calculate a simple perplexity estimate
            # (In a real implementation, you'd use a proper language model)
            perplexity = self._estimate_perplexity(post_texts)
            
            score = min(score, 1.0)
            
            explanation = self._generate_text_explanation(
                len(original_posts), avg_length, vocab_diversity, red_flags
            )
            
            return TextAnalysisResult(
                sample_posts=sample_posts,
                avg_perplexity=perplexity,
                repetitive_content=similarity_score > self.similarity_threshold,
                score=score,
                explanation=explanation
            )
            
        except Exception as e:
            logger.error(f"Text analysis error: {e}")
            return TextAnalysisResult(
                sample_posts=[],
                avg_perplexity=0.0,
                repetitive_content=False,
                score=0.5,
                explanation="Analysis failed - unable to assess text patterns"
            )
    
    def _calculate_text_similarity(self, texts: List[str]) -> float:
        """Calculate how similar texts are to each other"""
        if len(texts) < 2:
            return 0.0
        
        total_similarity = 0.0
        comparisons = 0
        
        # Compare each text to every other text
        for i in range(len(texts)):
            for j in range(i + 1, len(texts)):
                similarity = self._jaccard_similarity(texts[i], texts[j])
                total_similarity += similarity
                comparisons += 1
        
        return total_similarity / comparisons if comparisons > 0 else 0.0
    
    def _jaccard_similarity(self, text1: str, text2: str) -> float:
        """Calculate Jaccard similarity between two texts"""
        # Convert to sets of words (simple tokenization)
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        
        if not words1 and not words2:
            return 1.0  # Both empty
        if not words1 or not words2:
            return 0.0  # One empty
        
        intersection = len(words1.intersection(words2))
        union = len(words1.union(words2))
        
        return intersection / union
    
    def _count_ai_phrases(self, texts: List[str]) -> dict:
        """
        Comprehensive AI phrase detection with categorized results
        
        Returns:
            dict: Contains total count and breakdown by category
        """
        if not texts:
            return {"total": 0, "categories": {}, "phrases_found": []}
        
        combined_text = " ".join(texts).lower()
        category_counts = {}
        phrases_found = []
        total_count = 0
        
        # Check each category of AI phrases
        for category, phrase_list in self.ai_phrases.items():
            category_count = 0
            for phrase in phrase_list:
                if phrase.lower() in combined_text:
                    category_count += 1
                    total_count += 1
                    phrases_found.append(f"{category}: {phrase}")
            
            if category_count > 0:
                category_counts[category] = category_count
        
        # Additional pattern-based detection
        spam_count = self._count_spam_patterns(combined_text)
        human_indicators = self._count_human_indicators(combined_text)
        
        return {
            "total": total_count,
            "categories": category_counts,
            "phrases_found": phrases_found,
            "spam_patterns": spam_count,
            "human_indicators": human_indicators
        }
    
    def _count_spam_patterns(self, text: str) -> int:
        """Count spam/bot patterns in text"""
        count = 0
        for pattern in self.spam_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            count += len(matches)
        return count
    
    def _count_human_indicators(self, text: str) -> int:
        """Count patterns that suggest human authorship"""
        count = 0
        for pattern in self.human_indicators:
            matches = re.findall(pattern, text, re.IGNORECASE)
            count += len(matches)
        return count
    
    def _analyze_writing_style(self, texts: List[str]) -> dict:
        """
        Analyze writing style patterns for AI detection
        
        Returns:
            dict: Style analysis results
        """
        if not texts:
            return {"consistency": 0.0, "formality": 0.0, "complexity": 0.0}
        
        # Sentence length consistency (AI tends to be very consistent)
        sentence_lengths = []
        for text in texts:
            sentences = re.split(r'[.!?]+', text)
            for sentence in sentences:
                if sentence.strip():
                    sentence_lengths.append(len(sentence.strip().split()))
        
        if not sentence_lengths:
            return {"consistency": 0.0, "formality": 0.0, "complexity": 0.0}
        
        # Calculate consistency (lower variance = more consistent = more AI-like)
        import statistics
        if len(sentence_lengths) > 1:
            length_variance = statistics.variance(sentence_lengths)
            avg_length = statistics.mean(sentence_lengths)
            consistency = 1.0 - min(length_variance / max(avg_length, 1), 1.0)
        else:
            consistency = 1.0  # Single sentence is perfectly consistent
        
        # Formality score (count formal vs informal words)
        combined_text = " ".join(texts).lower()
        formal_words = ["therefore", "consequently", "furthermore", "moreover", "however", "nevertheless", "utilize", "implement", "facilitate"]
        informal_words = ["gonna", "wanna", "yeah", "nope", "cool", "awesome", "weird", "crazy", "super", "really"]
        
        formal_count = sum(1 for word in formal_words if word in combined_text)
        informal_count = sum(1 for word in informal_words if word in combined_text)
        
        total_formal_informal = formal_count + informal_count
        formality = formal_count / max(total_formal_informal, 1)
        
        # Complexity score (average words per sentence, subordinate clauses)
        total_words = len(combined_text.split())
        total_sentences = len(re.split(r'[.!?]+', combined_text))
        complexity = total_words / max(total_sentences, 1) / 20.0  # Normalize to 0-1
        
        return {
            "consistency": min(consistency, 1.0),
            "formality": min(formality, 1.0),
            "complexity": min(complexity, 1.0)
        }
    
    def _detect_template_usage(self, texts: List[str]) -> bool:
        """Detect if texts follow a template-like pattern"""
        if len(texts) < 3:
            return False
        
        # Look for repeated sentence structures
        structures = []
        for text in texts:
            # Simplify text structure (keep punctuation, remove specific words)
            structure = re.sub(r'\b[a-zA-Z]+\b', 'WORD', text)
            structures.append(structure)
        
        # Count unique structures
        unique_structures = len(set(structures))
        total_structures = len(structures)
        
        # If most posts have the same structure, it might be templated
        return unique_structures / total_structures < 0.5
    
    def _calculate_vocabulary_diversity(self, texts: List[str]) -> float:
        """Calculate vocabulary diversity (unique words / total words)"""
        all_words = []
        for text in texts:
            words = re.findall(r'\b[a-zA-Z]+\b', text.lower())
            all_words.extend(words)
        
        if not all_words:
            return 0.0
        
        unique_words = len(set(all_words))
        total_words = len(all_words)
        
        return unique_words / total_words
    
    def _estimate_perplexity(self, texts: List[str]) -> float:
        """
        Estimate text perplexity (simplified version)
        In a real implementation, this would use a proper language model
        """
        # This is a very simplified perplexity estimate
        # Real perplexity requires a trained language model
        
        if not texts:
            return 0.0
        
        # Count word frequencies
        word_counts = Counter()
        total_words = 0
        
        for text in texts:
            words = re.findall(r'\b[a-zA-Z]+\b', text.lower())
            word_counts.update(words)
            total_words += len(words)
        
        if total_words == 0:
            return 0.0
        
        # Calculate a simple entropy-based measure
        entropy = 0.0
        for count in word_counts.values():
            prob = count / total_words
            entropy += prob * math.log2(prob)
        
        # Convert to a perplexity-like measure (higher = more natural)
        return 2 ** (-entropy) if entropy < 0 else 1.0
    
    def _generate_text_explanation(self, num_posts: int, avg_length: float, 
                                 vocab_diversity: float, red_flags: List[str]) -> str:
        """Generate human-readable explanation of text analysis"""
        
        explanation = f"Analyzed {num_posts} original posts with average length {avg_length:.1f} words. "
        explanation += f"Vocabulary diversity: {vocab_diversity:.1%}. "
        
        if not red_flags:
            explanation += "Text patterns appear normal for human writing."
        else:
            explanation += f"Concerns: {', '.join(red_flags)}."
        
        return explanation