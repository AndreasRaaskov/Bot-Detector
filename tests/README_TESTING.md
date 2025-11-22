# 🧪 Testing Guide for Bot Detector

This guide helps team members understand and run tests for the Bot Detector project. Since we're a diverse team working across time zones, comprehensive testing ensures everyone's changes work correctly.

## 🚀 Quick Start

### Install Test Dependencies
```bash
# Make sure you're in the project root directory
cd Bot-Detector

# Install all dependencies including test tools
pip install -r backend/requirements.txt
```

### Run All Tests
```bash
# Run the complete test suite from project root
pytest

# Run tests with verbose output (recommended for first time)
pytest -v

# Run tests and show print statements (helpful for debugging)
pytest -v -s
```

## 📋 Test Categories

We organize tests into categories using pytest markers:

### Unit Tests
Test individual components in isolation:
```bash
pytest -m unit
```

### Integration Tests  
Test how components work together:
```bash
pytest -m integration
```

### API Tests
Test the FastAPI endpoints:
```bash
pytest -m api
```

### Slow Tests
Tests that take longer to run:
```bash
pytest -m "not slow"  # Skip slow tests
pytest -m slow        # Run only slow tests
```

## 📁 Test Files Overview

| File | Purpose | What it Tests |
|------|---------|---------------|
| `conftest.py` | Test configuration and shared fixtures | Test setup, mock data, utilities |
| `test_config.py` | Configuration system | .env files, JSON config, environment variables |
| `test_bluesky_client.py` | Bluesky API integration | Authentication, data fetching, error handling |
| `test_analyzers.py` | Bot detection algorithms | Follow analysis, posting patterns, text analysis |
| `test_api.py` | FastAPI endpoints | Request/response handling, validation, errors |
| `test_run_examples.py` | Documentation and examples | Manual testing guides, troubleshooting |

## 🔧 Running Specific Tests

### Run a Single Test File
```bash
pytest tests/test_config.py
pytest tests/test_analyzers.py
pytest tests/test_api.py
```

### Run a Specific Test Class
```bash
pytest tests/test_config.py::TestConfigFromJSON
pytest tests/test_analyzers.py::TestFollowAnalyzer
```

### Run a Specific Test Function
```bash
pytest tests/test_config.py::TestConfigFromJSON::test_load_from_json_file
```

### Run Tests Matching a Pattern
```bash
pytest -k "config"           # All tests with "config" in the name
pytest -k "bluesky"          # All tests with "bluesky" in the name
pytest -k "not slow"         # All tests except slow ones
```

## 📊 Test Coverage

Check how much of our code is covered by tests:

```bash
# Install coverage tool (if not already installed)
pip install pytest-cov

# Run tests with coverage
pytest --cov=.

# Generate detailed HTML coverage report
pytest --cov=. --cov-report=html

# Open coverage report
open htmlcov/index.html  # macOS
start htmlcov/index.html # Windows
xdg-open htmlcov/index.html # Linux
```

## 🛠️ Testing Different Configurations

Our tests verify the system works with different credential setups:

### Test with No Credentials
```bash
# Tests should pass even with no API keys configured
pytest tests/test_config.py::TestConfigInitialization::test_config_creation_with_no_files
```

### Test Configuration Priority
```bash
# Tests verify environment variables override JSON files
pytest tests/test_config.py::TestConfigPriority
```

### Test .env Folder Support
```bash
# Tests your .env/config.json setup
pytest tests/test_config.py::TestConfigFromEnvFolder
```

## 🌐 Manual API Testing

### Start the Server
```bash
cd backend
python main.py
```

### Test Endpoints with curl
```bash
# Health check
curl http://localhost:8000/health

# Configuration check
curl http://localhost:8000/config

# Analyze a user (example)
curl -X POST "http://localhost:8000/analyze" \
  -H "Content-Type: application/json" \
  -d '{"bluesky_handle": "example.bsky.social"}'
```

### Test with Different Tools

**Using httpie** (if installed):
```bash
http GET localhost:8000/health
http POST localhost:8000/analyze bluesky_handle=example.bsky.social
```

**Using Python requests**:
```python
import requests

# Health check
response = requests.get("http://localhost:8000/health")
print(response.json())

# Analyze user
response = requests.post(
    "http://localhost:8000/analyze",
    json={"bluesky_handle": "example.bsky.social"}
)
print(response.json())
```

## 🐛 Debugging Tests

### Run Tests with Debug Output
```bash
# Show print statements and detailed output
pytest -v -s

# Drop into debugger on failures
pytest --pdb

# Stop on first failure
pytest -x
```

### Common Test Issues

**Import Errors**:
```bash
# Make sure you're in the backend directory
cd backend

# Install dependencies
pip install -r requirements.txt
```

**Async Test Errors**:
```bash
# Make sure pytest-asyncio is installed
pip install pytest-asyncio

# Check that async tests use proper fixtures
# (See conftest.py for async examples)
```

**Mock Errors**:
- Check that mocks are set up before the code tries to use them
- Verify mock return values match expected data types
- Look at `conftest.py` for mock examples

## 📝 Writing New Tests

### Basic Test Structure
```python
import pytest
from your_module import YourClass

class TestYourFeature:
    """Test description for your feature"""
    
    def test_basic_functionality(self):
        """Test basic case"""
        # Arrange
        instance = YourClass()
        
        # Act
        result = instance.your_method("input")
        
        # Assert
        assert result == "expected_output"
    
    @pytest.mark.asyncio
    async def test_async_functionality(self):
        """Test async case"""
        instance = YourClass()
        result = await instance.async_method("input")
        assert result is not None
```

### Using Fixtures
```python
def test_with_fixture(self, sample_bluesky_profile):
    """Use fixtures from conftest.py"""
    assert sample_bluesky_profile.handle == "testuser.bsky.social"
```

### Marking Tests
```python
@pytest.mark.unit
def test_unit_example(self):
    """Unit test example"""
    pass

@pytest.mark.integration  
def test_integration_example(self):
    """Integration test example"""
    pass

@pytest.mark.slow
def test_slow_example(self):
    """Test that takes a long time"""
    pass
```

## 🔄 Continuous Integration

When Mitali sets up the GitHub repository, we'll add CI/CD that automatically runs tests:

### GitHub Actions Example
```yaml
# .github/workflows/test.yml
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
        with:
          python-version: 3.9
      - run: pip install -r backend/requirements.txt
      - run: cd backend && pytest
```

## 📚 Testing Philosophy

### What We Test
- ✅ **Configuration loading** - All credential methods work
- ✅ **API endpoints** - Requests and responses work correctly  
- ✅ **Bot detection logic** - Algorithms produce expected results
- ✅ **Error handling** - System handles failures gracefully
- ✅ **Data validation** - Invalid input is rejected properly

### What We Mock
- 🎭 **External APIs** - Bluesky, OpenAI, Anthropic, Google
- 🎭 **Network requests** - No real HTTP calls in unit tests
- 🎭 **File system** - Use temporary files for config tests
- 🎭 **Time** - Fixed timestamps for consistent test results

### Testing Best Practices
- 🎯 **Test behavior, not implementation** - Focus on what the code does
- 🔄 **Keep tests independent** - Each test should work in isolation  
- 📝 **Use descriptive names** - Make test purpose clear
- ⚡ **Fast feedback** - Unit tests should run quickly
- 🛡️ **Test edge cases** - What happens when things go wrong?

## 🆘 Getting Help

### Common Commands Reference
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=. --cov-report=html

# Run specific category
pytest -m unit

# Run specific file
pytest test_config.py

# Run with debug output
pytest -v -s

# Stop on first failure
pytest -x

# Run tests matching pattern
pytest -k "config"
```

### Troubleshooting
1. **Tests fail with import errors** → Check you're in `backend/` directory
2. **Async tests fail** → Install `pytest-asyncio`
3. **Coverage reports empty** → Install `pytest-cov`
4. **Tests hang** → Check for infinite loops or missing mocks
5. **Random test failures** → Look for tests that depend on external state

### Need Help?
- Check `test_run_examples.py` for comprehensive examples
- Look at existing tests for patterns to follow
- Ask team members (Andreas/Mitali) for technical questions
- Check pytest documentation: https://docs.pytest.org/

---

*Happy Testing! 🧪 Remember: Good tests make confident deployments possible.*