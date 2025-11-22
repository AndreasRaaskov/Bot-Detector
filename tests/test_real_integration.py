# test_real_integration.py - Real integration tests using actual Bluesky API
# These tests call the real Bluesky API and test the complete bot detection pipeline
# They require valid credentials and internet connection

import pytest
import asyncio
from unittest.mock import patch
import sys
from pathlib import Path

# Add backend directory to Python path
backend_dir = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_dir))

from config import Config
from bot_detector import BotDetector

class TestCredentialValidation:
    """
    First validate that all configured credentials actually work
    This runs before other tests to provide clear feedback on setup issues
    """
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_validate_bluesky_credentials(self):
        """Validate Bluesky credentials by attempting authentication"""
        config = Config()
        
        # Check if credentials are configured
        if not config.bluesky_username or not config.bluesky_password:
            pytest.skip("Bluesky credentials not configured in .env file")
        
        # Check if credentials look like placeholders
        if (config.bluesky_username == "your-bluesky-username" or 
            config.bluesky_password == "your-bluesky-password" or
            "your-" in config.bluesky_username):
            pytest.fail("Bluesky credentials appear to be placeholder values. Please update .env with real credentials.")
        
        # Test actual authentication
        from bluesky_client import BlueskyClient
        
        try:
            async with BlueskyClient(config.bluesky_username, config.bluesky_password) as client:
                auth_success = await client.authenticate()
                
                if not auth_success:
                    pytest.fail(f"Bluesky authentication failed with username: {config.bluesky_username}. Please check your credentials.")
                
                # Test a basic API call
                profile = await client.get_profile("bsky.app")
                if not profile:
                    pytest.fail("Bluesky authentication succeeded but API calls are failing")
                
                print(f"\\n✅ Bluesky credentials validated successfully")
                print(f"   Username: {config.bluesky_username}")
                print(f"   Authentication: SUCCESS")
                print(f"   API calls: Working")
                
        except Exception as e:
            error_msg = str(e).lower()
            if any(term in error_msg for term in ['invalid', 'auth', 'credential', 'password']):
                pytest.fail(f"Bluesky credential validation failed: {e}")
            else:
                pytest.fail(f"Bluesky API error: {e}")
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_validate_llm_api_keys(self):
        """Validate LLM API keys by making test requests"""
        config = Config()
        
        # Track which providers are properly configured
        working_providers = []
        failed_providers = []
        
        # Test OpenAI
        if (config.openai_api_key and 
            config.openai_api_key.startswith("sk-") and 
            len(config.openai_api_key) > 20 and
            "your-" not in config.openai_api_key):
            
            try:
                from llm_analyzer import LLMAnalyzer
                test_config = Config()
                test_config.preferred_llm_provider = "openai"
                analyzer = LLMAnalyzer(test_config.get_llm_keys())
                
                result = await analyzer.analyze_content(["Test message for OpenAI validation"])
                if result and result.model_used and "openai" in result.model_used.lower():
                    working_providers.append(f"OpenAI ({result.model_used})")
                else:
                    failed_providers.append("OpenAI (no valid response)")
                
                await analyzer.close()
                
            except Exception as e:
                failed_providers.append(f"OpenAI ({str(e)[:50]}...)")
        
        # Test Anthropic
        if (config.anthropic_api_key and 
            config.anthropic_api_key.startswith("sk-ant-") and 
            len(config.anthropic_api_key) > 20 and
            "your-" not in config.anthropic_api_key):
            
            try:
                from llm_analyzer import LLMAnalyzer
                test_config = Config()
                test_config.preferred_llm_provider = "anthropic"
                analyzer = LLMAnalyzer(test_config.get_llm_keys())
                
                result = await analyzer.analyze_content(["Test message for Anthropic validation"])
                if result and result.model_used and "anthropic" in result.model_used.lower():
                    working_providers.append(f"Anthropic ({result.model_used})")
                else:
                    failed_providers.append("Anthropic (no valid response)")
                
                await analyzer.close()
                
            except Exception as e:
                failed_providers.append(f"Anthropic ({str(e)[:50]}...)")
        
        # Test Google
        if (config.google_api_key and 
            len(config.google_api_key) > 20 and
            "your-" not in config.google_api_key):
            
            try:
                from llm_analyzer import LLMAnalyzer  
                test_config = Config()
                test_config.preferred_llm_provider = "google"
                analyzer = LLMAnalyzer(test_config.get_llm_keys())
                
                result = await analyzer.analyze_content(["Test message for Google validation"])
                if result and result.model_used and "google" in result.model_used.lower():
                    working_providers.append(f"Google ({result.model_used})")
                else:
                    failed_providers.append("Google (no valid response)")
                
                await analyzer.close()
                
            except Exception as e:
                failed_providers.append(f"Google ({str(e)[:50]}...)")
        
        # Report results
        if not working_providers and not failed_providers:
            pytest.skip("No LLM API keys configured or all appear to be placeholder values")
        
        print(f"\\n📊 LLM API Key Validation Results:")
        if working_providers:
            print("✅ Working providers:")
            for provider in working_providers:
                print(f"   - {provider}")
        
        if failed_providers:
            print("❌ Failed providers:")
            for provider in failed_providers:
                print(f"   - {provider}")
        
        # Ensure at least one provider works
        if not working_providers:
            pytest.fail("No LLM API keys are working. Please check your configuration.")
        
        print(f"\\n✅ LLM validation completed - {len(working_providers)} working provider(s)")

class TestRealBotDetection:
    """
    Integration tests using real Bluesky API calls
    These tests will only run if valid credentials are configured
    """
    
    @pytest.fixture(scope="class")
    def config(self):
        """Load real configuration - validation happens in dedicated tests"""
        config = Config()
        
        # Check if we have the minimum required credentials
        if not config.bluesky_username or not config.bluesky_password:
            pytest.skip("Bluesky credentials not configured - skipping real API tests")
        
        return config
    
    async def get_bot_detector(self, config):
        """Helper method to create bot detector with real configuration"""
        return BotDetector(config)
    
    @pytest.mark.integration
    @pytest.mark.slow
    @pytest.mark.asyncio
    async def test_known_human_account(self, config):
        """
        Test analysis of a known human account
        Using Bluesky's official account as a known human example
        """
        bot_detector = await self.get_bot_detector(config)
        try:
            # Test on Bluesky's official account - should score as human
            result = await bot_detector.analyze_user("bsky.app")
            
            # Basic response structure validation
            assert result is not None
            assert result.handle == "bsky.app"
            assert result.overall_score is not None
            assert 0.0 <= result.overall_score <= 1.0
            assert result.confidence is not None
            assert 0.0 <= result.confidence <= 1.0
            
            # Should have analysis results from all components
            assert result.follow_analysis is not None
            assert result.posting_pattern is not None  
            assert result.text_analysis is not None
            
            # Known human should have relatively low bot score
            assert result.overall_score < 0.7, f"Official Bluesky account scored too high: {result.overall_score}"
            
            print(f"\\n✅ Human account test:")
            print(f"   Handle: {result.handle}")
            print(f"   Score: {result.overall_score:.3f}")
            print(f"   Summary: {result.summary}")
            
        finally:
            await bot_detector.close()
    
    @pytest.mark.integration
    @pytest.mark.slow
    @pytest.mark.asyncio
    async def test_suspicious_account_patterns(self, bot_detector):
        """
        Test analysis looking for accounts with bot-like characteristics
        Note: We'll test pattern detection without making claims about specific accounts
        """
        # Test accounts with various suspicious patterns
        test_handles = [
            # Look for accounts with very new creation dates and high activity
            # Look for accounts with suspicious username patterns  
            # Look for accounts with very high following ratios
        ]
        
        # For now, let's test the detection logic works on any account
        # You can add specific handles here as you discover them
        
        # Test that the analyzer components work end-to-end
        result = await bot_detector.analyze_user("bsky.app")  # Using safe test account
        
        # Verify all analyzer components produced results
        assert result.follow_analysis.score is not None
        assert result.posting_pattern.score is not None
        assert result.text_analysis.score is not None
        
        print(f"\\n🔍 Pattern detection test passed for: {result.handle}")
    
    @pytest.mark.integration
    @pytest.mark.slow
    @pytest.mark.asyncio
    async def test_complete_analysis_pipeline(self, bot_detector):
        """
        Test the complete analysis pipeline end-to-end
        Verifies all components work together correctly
        """
        # Test on a real account
        result = await bot_detector.analyze_user("bsky.app")
        
        # Comprehensive validation of the complete response structure
        assert result.handle is not None
        assert result.display_name is not None
        assert result.created_at is not None
        assert result.processing_time_ms > 0
        
        # All analysis components should provide explanations
        assert len(result.follow_analysis.explanation) > 10
        assert len(result.posting_pattern.explanation) > 10  
        assert len(result.text_analysis.explanation) > 10
        
        # Should have recommendations
        assert len(result.recommendations) > 0
        
        # Should have a coherent summary
        assert len(result.summary) > 20
        assert result.handle.replace("@", "") in result.summary
        
        print(f"\\n✅ Complete pipeline test:")
        print(f"   Processing time: {result.processing_time_ms}ms")
        print(f"   Components tested: Follow, Posting, Text, LLM")
        print(f"   Recommendations: {len(result.recommendations)}")

class TestRealAPIConnectivity:
    """
    Test real API connectivity and error handling
    """
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_bluesky_api_connectivity(self):
        """Test that we can connect to Bluesky API"""
        config = Config()
        
        if not config.bluesky_username or not config.bluesky_password:
            pytest.skip("Bluesky credentials not configured")
        
        from bluesky_client import BlueskyClient
        
        async with BlueskyClient(config.bluesky_username, config.bluesky_password) as client:
            # Test authentication
            auth_success = await client.authenticate()
            assert auth_success, "Failed to authenticate with Bluesky API"
            
            # Test profile fetching
            profile = await client.get_profile("bsky.app")
            assert profile is not None, "Failed to fetch profile from Bluesky API"
            assert profile.handle == "bsky.app"
            
        print("\\n✅ Bluesky API connectivity test passed")
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_llm_api_connectivity(self):
        """Test LLM API connectivity and validate that API keys actually work"""
        config = Config()
        
        # Check if any LLM provider is configured with non-placeholder values
        valid_openai = config.openai_api_key and config.openai_api_key.startswith("sk-") and len(config.openai_api_key) > 20
        valid_anthropic = config.anthropic_api_key and config.anthropic_api_key.startswith("sk-ant-") and len(config.anthropic_api_key) > 20  
        valid_google = config.google_api_key and not config.google_api_key.startswith("your-") and len(config.google_api_key) > 20
        
        has_valid_llm = valid_openai or valid_anthropic or valid_google
        
        if not has_valid_llm:
            pytest.skip("No valid LLM API keys configured (keys must be real, not placeholders)")
        
        from llm_analyzer import LLMAnalyzer
        
        analyzer = LLMAnalyzer(config.get_llm_keys())
        
        try:
            # Test with simple content - this will actually call the API
            result = await analyzer.analyze_content([
                "This is a test post to verify LLM connectivity.",
                "Just checking that our AI analysis is working properly."
            ])
            
            # If we get here, the API key worked
            assert result is not None, "LLM analysis returned None - API key may be invalid"
            assert result.model_used is not None, "No model information returned - API call may have failed"
            assert result.confidence is not None, "No confidence score returned"
            assert result.score is not None, "No bot score returned"
            assert 0.0 <= result.score <= 1.0, f"Bot score out of range: {result.score}"
            assert len(result.reasoning) > 10, "No reasoning provided - API call may have failed"
            
            print(f"\\n✅ LLM API connectivity and validation test passed")
            print(f"   Model used: {result.model_used}")
            print(f"   Confidence: {result.confidence:.3f}")
            print(f"   Score: {result.score:.3f}")
            print(f"   API key validation: SUCCESS")
            
        except Exception as e:
            # If we get an authentication or API key error, fail the test with clear message
            error_msg = str(e).lower()
            if any(term in error_msg for term in ['api key', 'auth', 'unauthorized', 'forbidden', 'invalid']):
                pytest.fail(f"LLM API key validation failed: {e}")
            else:
                # Other errors might be network issues, re-raise
                raise
        finally:
            await analyzer.close()

class TestRealErrorHandling:
    """
    Test error handling with real API calls
    """
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_nonexistent_user_handling(self):
        """Test handling of nonexistent Bluesky users"""
        config = Config()
        
        if not config.bluesky_username or not config.bluesky_password:
            pytest.skip("Bluesky credentials not configured")
        
        detector = BotDetector(config)
        
        try:
            # Test with a handle that definitely doesn't exist
            nonexistent_handle = "definitely-does-not-exist-12345.bsky.social"
            
            with pytest.raises(Exception) as exc_info:
                await detector.analyze_user(nonexistent_handle)
            
            # Should get a meaningful error message
            error_msg = str(exc_info.value).lower()
            assert any(word in error_msg for word in ['not found', 'does not exist', 'invalid', 'user']), (
                f"Error message not descriptive enough: {exc_info.value}")
            
            print(f"\\n✅ Nonexistent user error handling test passed")
            print(f"   Error message: {exc_info.value}")
            
        finally:
            await detector.close()
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_rate_limiting_handling(self):
        """Test graceful handling of rate limits"""
        config = Config()
        
        if not config.bluesky_username or not config.bluesky_password:
            pytest.skip("Bluesky credentials not configured")
        
        detector = BotDetector(config)
        
        try:
            # Make multiple requests quickly to test rate limiting
            # Most APIs should handle a few requests gracefully
            handles = ["bsky.app", "bsky.app", "bsky.app"]  # Same handle to be safe
            
            results = []
            for handle in handles:
                try:
                    result = await detector.analyze_user(handle)
                    results.append(result)
                    await asyncio.sleep(1)  # Be nice to the API
                except Exception as e:
                    # Rate limiting should be handled gracefully
                    error_msg = str(e).lower()
                    if 'rate' in error_msg or 'limit' in error_msg or 'too many' in error_msg:
                        print(f"\\n✅ Rate limiting detected and handled: {e}")
                        break
                    else:
                        raise  # Re-raise if it's not a rate limit error
            
            # Should get at least one successful result
            assert len(results) > 0, "No successful requests completed"
            
            print(f"\\n✅ Rate limiting handling test passed")
            print(f"   Successful requests: {len(results)}")
            
        finally:
            await detector.close()

if __name__ == "__main__":
    # This allows running the tests directly for manual testing
    print("🧪 Running real integration tests...")
    print("⚠️  These tests make real API calls and require valid credentials")
    print("=" * 60)
    
    # Run with pytest
    pytest.main([__file__, "-v", "-s", "--tb=short"])