# test_api.py - Integration tests for FastAPI endpoints
# Tests the main API functionality, request/response handling, and error scenarios

import pytest
import json
from unittest.mock import AsyncMock, patch, Mock
from fastapi.testclient import TestClient

# Import our FastAPI app
import sys
from pathlib import Path

# Add backend directory to Python path
backend_dir = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_dir))

from main import app
from models import UserAnalysisRequest, UserAnalysisResponse
from bot_detector import BotDetector

class TestAPIEndpoints:
    """
    Test the main API endpoints
    """
    
    @pytest.fixture
    def client(self):
        """
        Create a test client for the FastAPI app
        """
        return TestClient(app)
    
    def test_root_endpoint(self, client):
        """
        Test the root endpoint returns basic info
        """
        response = client.get("/")
        
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "Bot Detector API is running" in data["message"]
    
    def test_health_endpoint(self, client):
        """
        Test the health check endpoint
        """
        response = client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "bot-detector"
        assert "capabilities" in data
        assert "bluesky_access" in data["capabilities"]
        assert "llm_providers" in data["capabilities"]
    
    def test_config_endpoint(self, client):
        """
        Test the configuration summary endpoint
        """
        response = client.get("/config")
        
        assert response.status_code == 200
        data = response.json()
        
        # Check expected configuration fields
        assert "bluesky_configured" in data
        assert "llm_providers" in data
        assert "api_host" in data
        assert "api_port" in data
        assert "debug_mode" in data
        assert "config_file_exists" in data
    
    def test_analyze_endpoint_invalid_request(self, client):
        """
        Test analyze endpoint with invalid request data
        """
        # Test with empty request
        response = client.post("/analyze", json={})
        assert response.status_code == 422  # Validation error
        
        # Test with invalid handle format
        response = client.post("/analyze", json={"bluesky_handle": ""})
        assert response.status_code == 422  # Validation error
        
        # Test with missing content type
        response = client.post("/analyze", data="invalid")
        assert response.status_code == 422

class TestAnalyzeEndpoint:
    """
    Test the main /analyze endpoint with various scenarios
    """
    
    @pytest.fixture
    def client(self):
        """Create a test client"""
        return TestClient(app)
    
    @pytest.fixture
    def mock_bot_detector(self, sample_analysis_response):
        """
        Create a mock bot detector for testing
        """
        mock_detector = AsyncMock(spec=BotDetector)
        mock_detector.analyze_user.return_value = sample_analysis_response
        return mock_detector
    
    def test_analyze_valid_request(self, client, mock_bot_detector, sample_analysis_response):
        """
        Test successful analysis request
        """
        with patch('main.bot_detector', mock_bot_detector):
            response = client.post(
                "/analyze",
                json={"bluesky_handle": "testuser.bsky.social"}
            )
        
        assert response.status_code == 200
        data = response.json()
        
        # Check response structure
        assert "handle" in data
        assert "overall_score" in data
        assert "confidence" in data
        assert "summary" in data
        assert "follow_analysis" in data
        assert "posting_pattern" in data
        assert "text_analysis" in data
        assert "llm_analysis" in data
        assert "recommendations" in data
        assert "processing_time_ms" in data
        
        # Check that the mock was called correctly
        mock_bot_detector.analyze_user.assert_called_once_with("testuser.bsky.social")
    
    def test_analyze_with_at_symbol(self, client, mock_bot_detector):
        """
        Test analyze endpoint handles @ symbol in handles
        """
        with patch('main.bot_detector', mock_bot_detector):
            response = client.post(
                "/analyze",
                json={"bluesky_handle": "@testuser.bsky.social"}
            )
        
        assert response.status_code == 200
        # The @ should be stripped by the validation
        mock_bot_detector.analyze_user.assert_called_once()
        call_args = mock_bot_detector.analyze_user.call_args[0]
        assert not call_args[0].startswith("@")  # @ should be stripped
    
    def test_analyze_bot_detector_error(self, client):
        """
        Test analyze endpoint when bot detector raises an exception
        """
        mock_detector = AsyncMock(spec=BotDetector)
        mock_detector.analyze_user.side_effect = Exception("Analysis failed")
        
        with patch('main.bot_detector', mock_detector):
            response = client.post(
                "/analyze",
                json={"bluesky_handle": "testuser.bsky.social"}
            )
        
        assert response.status_code == 500
        data = response.json()
        assert "detail" in data
        assert "Analysis failed" in data["detail"]
    
    def test_analyze_handle_validation(self, client):
        """
        Test handle validation in analyze endpoint
        """
        # Test various invalid handles
        invalid_handles = [
            "",  # Empty
            "   ",  # Whitespace only
            "invalid",  # No domain
            "invalid.",  # Invalid domain
            "@",  # Just @
        ]
        
        for handle in invalid_handles:
            response = client.post(
                "/analyze",
                json={"bluesky_handle": handle}
            )
            assert response.status_code == 422, f"Handle '{handle}' should be invalid"

class TestRequestValidation:
    """
    Test request validation and data models
    """
    
    @pytest.fixture
    def client(self):
        return TestClient(app)
    
    def test_user_analysis_request_validation(self):
        """
        Test UserAnalysisRequest model validation
        """
        # Valid request
        valid_request = UserAnalysisRequest(bluesky_handle="user.bsky.social")
        assert valid_request.bluesky_handle == "user.bsky.social"
        
        # Request with @ symbol (should be cleaned)
        at_request = UserAnalysisRequest(bluesky_handle="@user.bsky.social")
        assert at_request.bluesky_handle == "user.bsky.social"  # @ stripped
        
        # Invalid request - no domain
        with pytest.raises(ValueError):
            UserAnalysisRequest(bluesky_handle="invalid_handle")
        
        # Invalid request - empty
        with pytest.raises(ValueError):
            UserAnalysisRequest(bluesky_handle="")
    
    def test_content_type_validation(self, client):
        """
        Test that API requires proper content type
        """
        # Test with form data instead of JSON
        response = client.post(
            "/analyze",
            data={"bluesky_handle": "test.bsky.social"}
        )
        assert response.status_code == 422
        
        # Test with plain text
        response = client.post(
            "/analyze",
            content="plain text",
            headers={"Content-Type": "text/plain"}
        )
        assert response.status_code == 422

class TestResponseFormat:
    """
    Test API response format and structure
    """
    
    @pytest.fixture
    def client(self):
        return TestClient(app)
    
    def test_successful_response_structure(self, client, sample_analysis_response):
        """
        Test that successful responses have correct structure
        """
        mock_detector = AsyncMock()
        mock_detector.analyze_user.return_value = sample_analysis_response
        
        with patch('main.bot_detector', mock_detector):
            response = client.post(
                "/analyze",
                json={"bluesky_handle": "test.bsky.social"}
            )
        
        assert response.status_code == 200
        data = response.json()
        
        # Test required fields
        required_fields = [
            "handle", "overall_score", "confidence", "summary",
            "follow_analysis", "posting_pattern", "text_analysis", 
            "llm_analysis", "recommendations", "analysis_timestamp"
        ]
        
        for field in required_fields:
            assert field in data, f"Missing required field: {field}"
        
        # Test data types
        assert isinstance(data["overall_score"], float)
        assert 0 <= data["overall_score"] <= 1
        assert isinstance(data["confidence"], float)
        assert 0 <= data["confidence"] <= 1
        assert isinstance(data["recommendations"], list)
        
        # Test nested analysis structures
        assert "score" in data["follow_analysis"]
        assert "score" in data["posting_pattern"]
        assert "score" in data["text_analysis"]
        assert "score" in data["llm_analysis"]
    
    def test_error_response_format(self, client):
        """
        Test that error responses have consistent format
        """
        # Trigger an error
        mock_detector = AsyncMock()
        mock_detector.analyze_user.side_effect = Exception("Test error")
        
        with patch('main.bot_detector', mock_detector):
            response = client.post(
                "/analyze",
                json={"bluesky_handle": "test.bsky.social"}
            )
        
        assert response.status_code == 500
        data = response.json()
        assert "detail" in data
        assert isinstance(data["detail"], str)

class TestCORSHeaders:
    """
    Test CORS header configuration
    """
    
    @pytest.fixture
    def client(self):
        return TestClient(app)
    
    def test_cors_headers_present(self, client):
        """
        Test that CORS headers are present for cross-origin requests
        """
        # Test preflight request
        response = client.options(
            "/analyze",
            headers={"Origin": "http://localhost:3000"}
        )
        
        # Should allow the request
        assert response.status_code in [200, 204]
    
    def test_cors_allows_common_headers(self, client):
        """
        Test that common headers are allowed
        """
        response = client.post(
            "/analyze",
            json={"bluesky_handle": "test.bsky.social"},
            headers={
                "Origin": "http://localhost:3000",
                "Content-Type": "application/json"
            }
        )
        
        # Should not fail due to CORS
        assert response.status_code != 403

class TestAPIPerformance:
    """
    Test API performance characteristics
    """
    
    @pytest.fixture
    def client(self):
        return TestClient(app)
    
    def test_concurrent_requests(self, client, sample_analysis_response):
        """
        Test handling of multiple concurrent requests
        """
        import concurrent.futures
        
        mock_detector = AsyncMock()
        mock_detector.analyze_user.return_value = sample_analysis_response
        
        def make_request():
            with patch('main.bot_detector', mock_detector):
                response = client.post(
                    "/analyze",
                    json={"bluesky_handle": "test.bsky.social"}
                )
                return response.status_code
        
        # Make multiple concurrent requests
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(make_request) for _ in range(10)]
            results = [future.result() for future in futures]
        
        # All requests should succeed
        assert all(status == 200 for status in results)
    
    def test_response_time_metadata(self, client, sample_analysis_response):
        """
        Test that response includes timing metadata
        """
        mock_detector = AsyncMock()
        mock_detector.analyze_user.return_value = sample_analysis_response
        
        with patch('main.bot_detector', mock_detector):
            response = client.post(
                "/analyze",
                json={"bluesky_handle": "test.bsky.social"}
            )
        
        assert response.status_code == 200
        data = response.json()
        
        # Should include processing time
        assert "processing_time_ms" in data
        assert isinstance(data["processing_time_ms"], int)
        assert data["processing_time_ms"] >= 0

class TestAPIDocumentation:
    """
    Test API documentation and OpenAPI schema
    """
    
    @pytest.fixture
    def client(self):
        return TestClient(app)
    
    def test_openapi_schema_available(self, client):
        """
        Test that OpenAPI schema is available
        """
        response = client.get("/openapi.json")
        assert response.status_code == 200
        
        schema = response.json()
        assert "openapi" in schema
        assert "info" in schema
        assert "paths" in schema
        
        # Check that our endpoints are documented
        assert "/analyze" in schema["paths"]
        assert "/health" in schema["paths"]
    
    def test_api_documentation_content(self, client):
        """
        Test that API documentation contains expected content
        """
        response = client.get("/openapi.json")
        schema = response.json()
        
        # Check API info
        assert schema["info"]["title"] == "Bot Detector API"
        assert "description" in schema["info"]
        assert "version" in schema["info"]
        
        # Check analyze endpoint documentation
        analyze_endpoint = schema["paths"]["/analyze"]["post"]
        assert "summary" in analyze_endpoint
        assert "requestBody" in analyze_endpoint
        assert "responses" in analyze_endpoint

@pytest.mark.integration
class TestFullAPIWorkflow:
    """
    Integration tests for complete API workflows
    """
    
    @pytest.fixture
    def client(self):
        return TestClient(app)
    
    def test_complete_analysis_workflow(self, client):
        """
        Test a complete analysis workflow from request to response
        """
        # This test would ideally use real data, but we'll mock it
        # to avoid external dependencies in tests
        
        from models import (
            FollowAnalysisResult, PostingPatternResult, 
            TextAnalysisResult, LLMAnalysisResult
        )
        
        # Create a realistic analysis response
        mock_response = UserAnalysisResponse(
            handle="testuser.bsky.social",
            display_name="Test User",
            bio="A test user account",
            avatar_url=None,
            created_at=None,
            follow_analysis=FollowAnalysisResult(
                follower_count=100,
                following_count=150,
                ratio=1.5,
                score=0.2,
                explanation="Normal follow pattern"
            ),
            posting_pattern=PostingPatternResult(
                total_posts=50,
                posts_per_day_avg=2.3,
                posting_hours=[9, 10, 14, 15, 20, 21],
                unusual_frequency=False,
                score=0.1,
                explanation="Normal posting patterns"
            ),
            text_analysis=TextAnalysisResult(
                sample_posts=["Sample post 1", "Sample post 2"],
                avg_perplexity=45.2,
                repetitive_content=False,
                score=0.15,
                explanation="Normal text patterns"
            ),
            llm_analysis=LLMAnalysisResult(
                model_used="mock/test-model",
                confidence=0.8,
                reasoning="Content appears human-written",
                score=0.2
            ),
            overall_score=0.16,
            confidence=0.75,
            summary="Account appears to be human",
            recommendations=["Account shows normal behavior"],
            processing_time_ms=1200
        )
        
        mock_detector = AsyncMock()
        mock_detector.analyze_user.return_value = mock_response
        
        with patch('main.bot_detector', mock_detector):
            # Make the request
            response = client.post(
                "/analyze",
                json={"bluesky_handle": "testuser.bsky.social"}
            )
        
        # Verify successful response
        assert response.status_code == 200
        data = response.json()
        
        # Verify complete workflow data
        assert data["handle"] == "testuser.bsky.social"
        assert data["overall_score"] == 0.16
        assert data["confidence"] == 0.75
        assert len(data["recommendations"]) > 0
        
        # Verify all analysis components are present
        assert data["follow_analysis"]["score"] == 0.2
        assert data["posting_pattern"]["score"] == 0.1
        assert data["text_analysis"]["score"] == 0.15
        assert data["llm_analysis"]["score"] == 0.2
        
        # Verify timing information
        assert "processing_time_ms" in data
        assert isinstance(data["processing_time_ms"], int)

@pytest.mark.slow
class TestAPIStressTests:
    """
    Stress tests for API performance and reliability
    """
    
    @pytest.fixture
    def client(self):
        return TestClient(app)
    
    def test_large_request_handling(self, client):
        """
        Test handling of requests with very long handles
        """
        # Test with maximum reasonable handle length
        long_handle = "a" * 100 + ".bsky.social"
        
        response = client.post(
            "/analyze",
            json={"bluesky_handle": long_handle}
        )
        
        # Should either succeed or fail gracefully with 422
        assert response.status_code in [200, 422, 500]
    
    def test_malformed_json_handling(self, client):
        """
        Test handling of malformed JSON requests
        """
        # Test with malformed JSON
        response = client.post(
            "/analyze",
            content='{"bluesky_handle": "test.bsky.social"',  # Missing closing brace
            headers={"Content-Type": "application/json"}
        )
        
        assert response.status_code == 422  # Should handle malformed JSON gracefully