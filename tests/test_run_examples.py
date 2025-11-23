# test_run_examples.py - Example test runs and documentation
# This file shows team members how to run different types of tests
# It also includes some practical examples for manual testing

"""
=================================================================
TEST RUNNING EXAMPLES FOR THE BOT DETECTOR PROJECT
=================================================================

This file contains examples of how to run tests and what to expect.
It's designed to help team members understand the testing system.

QUICK START - Running Tests:

1. Install test dependencies:
   pip install -r requirements.txt

2. Run all tests:
   pytest

3. Run specific test categories:
   pytest -m unit          # Only unit tests
   pytest -m integration   # Only integration tests
   pytest -m api          # Only API tests

4. Run tests with coverage:
   pytest --cov=. --cov-report=html

5. Run tests verbosely:
   pytest -v -s

6. Run a specific test file:
   pytest test_config.py

7. Run a specific test:
   pytest test_config.py::TestConfigInitialization::test_config_creation_with_no_files

=================================================================
"""

import pytest
import json
import asyncio
from pathlib import Path

class TestExampleScenarios:
    """
    Example test scenarios that demonstrate common use cases
    These tests show what different types of users and behaviors look like
    """
    
    def test_typical_human_user_profile(self):
        """
        Example: What a typical human user looks like in our system
        This test documents the expected characteristics of real users
        """
        # Typical human user characteristics
        human_profile = {
            "followers_count": 150,
            "following_count": 200, 
            "posts_count": 500,
            "follow_ratio": 200/150,  # 1.33 - reasonable ratio
            "posts_per_day": 2.5,     # Moderate posting
            "vocabulary_diversity": 0.75,  # Good variety in language
            "ai_phrase_count": 0,     # No AI-typical phrases
            "posting_hours_count": 8, # Posts during 8 different hours
            "repost_ratio": 0.3      # 30% reposts, 70% original
        }
        
        # Human users should have low bot scores
        assert human_profile["follow_ratio"] < 5.0
        assert human_profile["posts_per_day"] < 20
        assert human_profile["vocabulary_diversity"] > 0.5
        assert human_profile["ai_phrase_count"] == 0
        assert human_profile["repost_ratio"] < 0.8
        
        print("✅ Human user profile passes all checks")
    
    def test_typical_bot_profile(self):
        """
        Example: What a typical bot looks like in our system
        This test documents the characteristics we expect from bots
        """
        # Typical bot characteristics  
        bot_profile = {
            "followers_count": 5,
            "following_count": 2500,
            "posts_count": 10000,
            "follow_ratio": 2500/5,   # 500.0 - very high ratio
            "posts_per_day": 150,     # Very high posting frequency
            "vocabulary_diversity": 0.25,  # Low variety (repetitive)
            "ai_phrase_count": 5,     # Multiple AI-typical phrases
            "posting_hours_count": 24, # Posts at all hours (no sleep)
            "repost_ratio": 0.9       # 90% reposts, little original content
        }
        
        # Bots should trigger multiple red flags
        assert bot_profile["follow_ratio"] > 10.0  # High follow ratio
        assert bot_profile["posts_per_day"] > 50   # Excessive posting
        assert bot_profile["vocabulary_diversity"] < 0.4  # Low diversity
        assert bot_profile["ai_phrase_count"] > 0   # AI phrases present
        assert bot_profile["repost_ratio"] > 0.8    # Mostly reposts
        
        print("🤖 Bot profile triggers expected red flags")
    
    def test_edge_case_new_user(self):
        """
        Example: New user that might be falsely flagged
        Shows how our system should handle edge cases gracefully
        """
        # Brand new user characteristics
        new_user_profile = {
            "followers_count": 0,      # No followers yet
            "following_count": 50,     # Following some people
            "posts_count": 3,          # Just a few posts
            "account_age_days": 1,     # Created yesterday
            "posts_per_day": 3,        # All posts from first day
            "follow_ratio": 1000.0  # Very high ratio for 0 followers (indicates likely bot)
        }
        
        # New users should get some leniency in scoring
        # The system should recognize this as a new user pattern
        assert new_user_profile["account_age_days"] < 30
        assert new_user_profile["posts_count"] < 10
        
        print("👶 New user profile recognized - should get leniency")

class TestManualTestingHelpers:
    """
    Helper functions for manual testing and debugging
    These aren't automated tests but examples of how to test manually
    """
    
    def test_example_api_requests(self):
        """
        Example API requests for manual testing
        Shows the team how to test the API manually
        """
        # Example requests that team members can use
        example_requests = [
            {
                "description": "Normal user analysis",
                "request": {"bluesky_handle": "normal.bsky.social"},
                "expected_score_range": (0.0, 0.4)
            },
            {
                "description": "Suspicious user analysis", 
                "request": {"bluesky_handle": "suspicious.bsky.social"},
                "expected_score_range": (0.6, 1.0)
            },
            {
                "description": "Handle with @ symbol",
                "request": {"bluesky_handle": "@user.bsky.social"},
                "expected_behavior": "@ symbol should be stripped"
            }
        ]
        
        for example in example_requests:
            print(f"📝 {example['description']}")
            print(f"   Request: {example['request']}")
            if 'expected_score_range' in example:
                print(f"   Expected score: {example['expected_score_range'][0]}-{example['expected_score_range'][1]}")
            if 'expected_behavior' in example:
                print(f"   Expected: {example['expected_behavior']}")
            print()
        
        assert len(example_requests) > 0  # Just to make pytest happy
    
    def test_curl_examples(self):
        """
        Example curl commands for testing the API
        Useful for team members who prefer command-line testing
        """
        base_url = "http://localhost:8000"
        
        curl_examples = [
            {
                "description": "Health check",
                "command": f'curl -X GET "{base_url}/health"'
            },
            {
                "description": "Basic user analysis",
                "command": f'''curl -X POST "{base_url}/analyze" \\
     -H "Content-Type: application/json" \\
     -d '{{"bluesky_handle": "test.bsky.social"}}\''''
            },
            {
                "description": "Configuration check",
                "command": f'curl -X GET "{base_url}/config"'
            }
        ]
        
        print("🌐 Curl command examples:")
        print("=" * 50)
        for example in curl_examples:
            print(f"{example['description']}:")
            print(example['command'])
            print()
        
        assert len(curl_examples) > 0

class TestConfigurationExamples:
    """
    Examples of different configuration setups
    Helps team members understand how to configure the system
    """
    
    def test_minimal_configuration(self):
        """
        Example: Minimal configuration to get started
        Shows what's needed for basic functionality
        """
        minimal_config = {
            "bluesky": {
                "username": "your-username",
                "password": "your-password"
            }
            # No LLM keys - will work with limited functionality
        }
        
        print("🔧 Minimal configuration (Bluesky only):")
        print(json.dumps(minimal_config, indent=2))
        print("This enables basic analysis without LLM features")
        
        assert "bluesky" in minimal_config
    
    def test_full_configuration(self):
        """
        Example: Full configuration with all features enabled
        Shows the complete setup for maximum functionality
        """
        full_config = {
            "bluesky": {
                "username": "your-bluesky-username",
                "password": "your-bluesky-password"
            },
            "llm": {
                "openai_api_key": "sk-your-openai-key",
                "anthropic_api_key": "sk-ant-your-anthropic-key",
                "google_api_key": "your-google-key",
                "preferred_provider": "openai"
            },
            "api": {
                "host": "0.0.0.0",
                "port": 8000,
                "debug": False
            }
        }
        
        print("🚀 Full configuration (all features):")
        print(json.dumps(full_config, indent=2))
        print("This enables all analysis features")
        
        assert "bluesky" in full_config
        assert "llm" in full_config
        assert "api" in full_config
    
    def test_environment_variables_example(self):
        """
        Example: Setting up with environment variables
        Shows how to use environment variables instead of config files
        """
        env_example = {
            "BLUESKY_USERNAME": "your-username",
            "BLUESKY_PASSWORD": "your-password", 
            "OPENAI_API_KEY": "sk-your-openai-key",
            "PREFERRED_LLM_PROVIDER": "openai",
            "API_PORT": "8000",
            "DEBUG_MODE": "false"
        }
        
        print("🌍 Environment variables example:")
        for key, value in env_example.items():
            print(f"export {key}={value}")
        
        assert len(env_example) > 0

class TestTroubleshootingExamples:
    """
    Common issues and their solutions
    Helps team members debug problems they might encounter
    """
    
    def test_common_errors_and_solutions(self):
        """
        Example: Common error scenarios and how to fix them
        Documents typical problems team members might face
        """
        common_issues = [
            {
                "error": "No module named 'fastapi'",
                "solution": "Run: pip install -r requirements.txt",
                "cause": "Dependencies not installed"
            },
            {
                "error": "Configuration validation failed",
                "solution": "Check your .env or config.json file format",
                "cause": "Invalid configuration file"
            },
            {
                "error": "Connection refused to localhost:8000",
                "solution": "Make sure the server is running: python main.py",
                "cause": "Server not started"
            },
            {
                "error": "422 Validation Error",
                "solution": "Check that bluesky_handle includes a domain (e.g., user.bsky.social)",
                "cause": "Invalid request format"
            },
            {
                "error": "python-dotenv not installed",
                "solution": "Run: pip install python-dotenv",
                "cause": "Missing optional dependency for .env file support"
            }
        ]
        
        print("🔧 Common issues and solutions:")
        print("=" * 50)
        for issue in common_issues:
            print(f"❌ Error: {issue['error']}")
            print(f"✅ Solution: {issue['solution']}")
            print(f"💡 Cause: {issue['cause']}")
            print()
        
        assert len(common_issues) > 0

@pytest.mark.slow
class TestPerformanceExamples:
    """
    Performance testing examples
    Shows how to test system performance and identify bottlenecks
    """
    
    def test_response_time_expectations(self):
        """
        Example: Expected response times for different operations
        Documents performance expectations for the system
        """
        performance_expectations = {
            "health_check": {"max_time_ms": 100, "description": "Health endpoint"},
            "config_check": {"max_time_ms": 200, "description": "Configuration endpoint"},
            "basic_analysis": {"max_time_ms": 5000, "description": "User analysis without LLM"},
            "full_analysis": {"max_time_ms": 15000, "description": "User analysis with LLM"},
            "concurrent_requests": {"max_time_ms": 10000, "description": "10 concurrent analyses"}
        }
        
        print("⏱️  Performance expectations:")
        for operation, expectations in performance_expectations.items():
            print(f"{expectations['description']}: <{expectations['max_time_ms']}ms")
        
        assert len(performance_expectations) > 0

if __name__ == "__main__":
    print("🧪 Bot Detector Test Examples")
    print("=" * 40)
    print("Run with: pytest test_run_examples.py -v -s")
    print("This will show all the examples and documentation.")
    print()
    print("For interactive exploration, try:")
    print("pytest test_run_examples.py::TestManualTestingHelpers::test_curl_examples -v -s")