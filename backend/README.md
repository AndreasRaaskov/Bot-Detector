# Bot Detector Backend

A FastAPI-based backend service for detecting bots on Bluesky using multiple analysis methods including follower patterns, posting behavior, text analysis, and LLM-powered content assessment.

## 🚀 Quick Start

### 1. Install Dependencies

**On Linux/macOS:**
```bash
# Navigate to backend directory
cd backend

# Create virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate

# Install requirements
pip install -r requirements.txt
```

**On Windows:**
```cmd
:: Navigate to backend directory
cd backend

:: Create virtual environment (recommended)  
python -m venv venv
venv\Scripts\activate

:: Install requirements
pip install -r requirements.txt
```

### 2. Configure Credentials (Choose ONE method)

**🔹 Method A: .env Folder (Team Standard)**

1. Copy the example .env folder:
   ```bash
   # Linux/macOS
   cp -r ../.env.example .env
   
   # Windows  
   xcopy /E /I ..\.env.example .env
   ```

2. Edit `.env/config.json` with your real credentials:
   ```json
   {
     "bluesky": {
       "username": "your-actual-username",
       "password": "your-actual-password"
     },
     "llm": {
       "openai_api_key": "sk-your-real-key"
     }
   }
   ```

**🔹 Method A-Alt: .env File (Standard)**

1. Create a `.env` file:
   ```bash
   BLUESKY_USERNAME=your-actual-username
   BLUESKY_PASSWORD=your-actual-password
   OPENAI_API_KEY=sk-your-real-openai-key
   # ... etc
   ```

**🔹 Method B: JSON Config File**

Create a `config.json` file in the backend directory:
```json
{
  "bluesky": {
    "username": "your-bluesky-username-or-email",
    "password": "your-bluesky-password"
  },
  "llm": {
    "openai_api_key": "sk-your-openai-key-here",
    "anthropic_api_key": "sk-ant-your-anthropic-key-here",
    "google_api_key": "your-google-api-key-here",
    "preferred_provider": "openai"
  }
}
```

**🔹 Method C: Environment Variables**

**Linux/macOS:**
```bash
export BLUESKY_USERNAME="your-username"
export BLUESKY_PASSWORD="your-password"  
export OPENAI_API_KEY="sk-..."
export ANTHROPIC_API_KEY="sk-ant-..."
export GOOGLE_API_KEY="..."
```

**Windows:**
```cmd
set BLUESKY_USERNAME=your-username
set BLUESKY_PASSWORD=your-password
set OPENAI_API_KEY=sk-...
set ANTHROPIC_API_KEY=sk-ant-...
set GOOGLE_API_KEY=...
```

### 3. Run the Server

**All Platforms:**
```bash
python main.py
```

The API will be available at `http://localhost:8000`

### 🔒 Security Notes

- ✅ `.env` and `config.json` are in `.gitignore` - they won't be committed
- ✅ Only `.env.example` is committed as a template
- ✅ Configuration priority: Environment Variables > config.json > .env file
- ⚠️ **Never commit real API keys or passwords to git!**

## 📊 API Endpoints

### Analyze User
```http
POST /analyze
Content-Type: application/json

{
  "bluesky_handle": "example.bsky.social"
}
```

Returns comprehensive bot analysis including:
- Follow/follower ratio analysis
- Posting pattern detection
- Text content analysis
- LLM-powered assessment
- Overall bot score (0-1, higher = more likely bot)

### Health Check
```http
GET /health
```

Returns service status and available capabilities.

### Configuration
```http
GET /config
```

Returns configuration summary (no sensitive data exposed).

## 🔧 Architecture

The system uses a modular architecture with these components:

- **`main.py`** - FastAPI application and API endpoints
- **`bot_detector.py`** - Main orchestrator that coordinates all analysis methods
- **`bluesky_client.py`** - Handles Bluesky AT Protocol API communication
- **`analyzers.py`** - Contains follow, posting pattern, and text analysis logic
- **`llm_analyzer.py`** - Model-agnostic LLM integration for AI content detection
- **`config.py`** - Configuration management from files and environment variables
- **`models.py`** - Pydantic data models for API requests and responses

## 🔍 Analysis Methods

### 1. Follow/Follower Analysis
- Detects accounts that follow many but have few followers
- Identifies suspiciously round numbers
- Flags accounts with zero followers but high activity

### 2. Posting Pattern Analysis
- Analyzes posting frequency and timing
- Detects 24/7 posting without sleep patterns
- Identifies burst posting and regular intervals
- Calculates repost-to-original content ratio

### 3. Text Content Analysis
- Measures vocabulary diversity
- Detects repetitive or template-like content
- Identifies AI-typical phrases
- Calculates text similarity between posts

### 4. LLM Analysis
- Sends content to AI models for human vs. AI assessment
- Supports OpenAI GPT, Anthropic Claude, Google Gemini
- Includes local model support via Ollama
- Provides reasoning for AI decisions

## ⚙️ Configuration Options

### Minimum Requirements
The system needs either:
- Bluesky credentials (for data fetching), OR
- At least one LLM API key (for analysis)

### Recommended Setup
- Bluesky credentials for full data access
- At least one LLM provider for AI-powered analysis
- Multiple LLM providers for redundancy

### LLM Providers Supported
- **OpenAI** - GPT models (requires API key)
- **Anthropic** - Claude models (requires API key)
- **Google** - Gemini models (requires API key)
- **Ollama** - Local models (requires Ollama installation)

## 🔒 Security Notes

- API keys are never logged or exposed in responses
- Configuration supports both files and environment variables
- All external API calls include proper error handling
- Input validation prevents injection attacks

## 🧪 Development

### Run Tests
```bash
pytest
```

### Code Formatting
```bash
black .
flake8 .
mypy .
```

### Debug Mode
Set `"debug": true` in config.json or `DEBUG_MODE=true` environment variable.

## 📝 Example Usage

```python
import httpx
import asyncio

async def analyze_user():
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8000/analyze",
            json={"bluesky_handle": "example.bsky.social"}
        )
        result = response.json()
        print(f"Bot score: {result['overall_score']:.2f}")
        print(f"Summary: {result['summary']}")

asyncio.run(analyze_user())
```

## 🤝 Contributing

This is a hackathon project developed by a diverse team across time zones. All code includes extensive comments for accessibility.

Team members:
- Technical: Andreas (MS.c Human-Centered AI), Mitali (BA Computer Science)
- Policy: Matt, Clare
- AI: Claude Code (backend), Lovable (frontend)

## 📄 License

Developed for Apart Research hackathon focusing on detecting automated misinformation campaigns.