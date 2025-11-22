# 🤖 Bot Detector

**Detecting automated misinformation campaigns on Bluesky using multi-method analysis**

A hackathon project for [Apart Research](https://apartresearch.com/) focused on developing better methods to detect automated misinformation campaigns using AI-powered analysis techniques.

## 🎯 Project Overview

Bot Detector combines multiple analysis methods to identify potential bot accounts on Bluesky:

- **📊 Follow/Follower Analysis** - Detects suspicious ratios and patterns
- **⏰ Posting Pattern Analysis** - Identifies inhuman timing and frequency  
- **📝 Text Content Analysis** - Detects repetitive content and AI phrases
- **🧠 LLM Analysis** - AI-powered content assessment for AI vs. human detection
- **🔗 Network Analysis** - *Future: Coordinated behavior detection*
- **📈 Real-time Monitoring** - *Future: Live bot detection dashboard*

## 👥 Team

**Human Team Members:**
- **Technical**: Andreas (MS.c Human-Centered AI), Mitali (BA Computer Science)  
- **Policy**: Matt, Clare

**AI Team Members:**
- **Backend**: Claude Code
- **Frontend**: Lovable

*Working across different time zones with diverse backgrounds - all code includes extensive documentation for team accessibility.*

## 🏗️ Architecture

```
Bot-Detector/
├── backend/              # FastAPI backend service
│   ├── main.py          # API server and endpoints
│   ├── bot_detector.py  # Main analysis orchestrator
│   ├── bluesky_client.py # Bluesky AT Protocol client
│   ├── analyzers.py     # Core detection algorithms
│   ├── llm_analyzer.py  # Multi-provider LLM integration
│   ├── config.py        # Configuration management
│   ├── models.py        # Data models and validation
│   ├── .env.example     # Environment template
│   └── requirements.txt # Python dependencies
├── tests/               # Test suite
│   ├── test_config.py   # Configuration tests
│   ├── test_api.py      # API endpoint tests
│   ├── test_analyzers.py # Bot detection logic tests
│   ├── test_bluesky_client.py # Bluesky integration tests
│   └── README_TESTING.md # Testing documentation
├── frontend/            # React web interface with shadcn/ui
│   ├── src/             # React source code
│   ├── dist/            # Built frontend (served by backend)
│   ├── package.json     # Node.js dependencies
│   └── vite.config.ts   # Vite configuration
├── pytest.ini          # Test configuration
├── .gitignore          # Prevents committing secrets
└── README.md           # This file
```

## 🚀 Quick Start

### Prerequisites
- Python 3.8+ 
- Node.js 18+ (for frontend)
- Git
- API keys for at least one service (Bluesky or LLM providers)

### Setup Instructions

**1. Clone and Navigate**
```bash
git clone <repository-url>
cd Bot-Detector
```

**2. Install Backend Dependencies**

*Linux/macOS:*
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r backend/requirements.txt
```

*Windows:*
```cmd
python -m venv venv
venv\Scripts\activate  
pip install -r backend\requirements.txt
```

**3. Install Frontend Dependencies**
```bash
cd frontend
npm install
cd ..
```

**4. Configure Credentials**

Copy the environment template:
```bash
# Linux/macOS
cp config.example.json config.json

# Windows
copy config.example.json config.json
```

Edit `config.json` with your credentials:
```json
{
  "bluesky": {
    "username": "your-bluesky-username",
    "password": "your-bluesky-password"
  },
  "llm": {
    "openai_api_key": "sk-your-openai-key"
  }
}
```

**5. Choose Your Running Mode**

### 🔧 Development Mode (Recommended for Development)
Runs frontend and backend as separate services with hot reload:

```bash
./run_dev.sh
```

This starts:
- Backend API server: `http://localhost:8000`
- Frontend dev server: `http://localhost:8080` (with API proxy)

### 🚀 Production Mode (Integrated)
Builds frontend and serves it through the backend:

```bash
./serve_prod.sh
```

This serves everything from: `http://localhost:8000`
- Frontend routes: `/`, `/about`, etc.
- API routes: `/analyze`, `/health`, `/config`

**6. Test the Application**

Visit the appropriate URL based on your running mode:
- Development: `http://localhost:8080` (frontend with API proxy to backend on :8000)
- Production: `http://localhost:8000` (integrated backend serving frontend)

### 🔍 Troubleshooting Development Mode

If the frontend can't connect to the backend API:

1. **Check both services are running**:
   ```bash
   # In one terminal - this starts BOTH backend and frontend
   ./run_dev.sh
   ```

2. **Verify backend is accessible**:
   ```bash
   # In another terminal
   curl http://localhost:8000/health
   ```

3. **Check frontend proxy configuration** - the Vite config should proxy `/analyze`, `/health`, and `/config` to `http://localhost:8000`

**7. Run Tests** (Optional but recommended)
```bash
# From project root
pytest
```

Analyze a user:
```bash
curl -X POST "http://localhost:8000/analyze" \
  -H "Content-Type: application/json" \
  -d '{"bluesky_handle": "example.bsky.social"}'
```

## 🔧 Configuration Options

### API Keys Needed

**Bluesky Access** *(recommended)*:
- Username and password for your Bluesky account
- Enables full data fetching capabilities

**LLM Providers** *(at least one recommended)*:
- **OpenAI**: Get key from [platform.openai.com](https://platform.openai.com/api-keys)
- **Anthropic**: Get key from [console.anthropic.com](https://console.anthropic.com/)
- **Google**: Get key from [aistudio.google.com](https://aistudio.google.com/app/apikey)
- **Ollama**: Local models (install separately from [ollama.ai](https://ollama.ai/))

### Configuration Priority
1. **Environment Variables** (highest priority)
2. **config.json** file
3. **.env** file (lowest priority)

### Minimum Requirements
The system needs either:
- Bluesky credentials (for data fetching), OR  
- At least one LLM API key (for analysis)

*Ideally both for full functionality.*

## 🔬 Detection Methods

### Follow/Follower Analysis
- High following-to-follower ratios
- Suspiciously round numbers
- Zero followers on established accounts

### Posting Pattern Analysis  
- Inhuman posting frequencies (>100 posts/day)
- No sleep patterns (24/7 posting)
- Perfectly regular intervals
- High repost-to-original ratios

### Text Content Analysis
- Vocabulary diversity measurement
- Repetitive or template-like content
- AI-typical phrases detection
- Cross-post similarity analysis

### LLM Analysis
- AI vs. human content assessment
- Multi-model consensus for reliability
- Confidence scoring and reasoning
- Model-agnostic architecture

## 🔒 Security & Privacy

- ✅ All credentials stored locally (never sent to our servers)
- ✅ API keys protected by `.gitignore` 
- ✅ No sensitive data logging
- ✅ Read-only Bluesky access
- ✅ Configurable analysis depth

## 🎯 Roadmap

### ✅ MVP (Current)
- [x] Multi-method bot detection
- [x] Bluesky integration
- [x] LLM analysis support
- [x] REST API interface
- [x] Web frontend interface (React + shadcn/ui)
- [x] Integrated backend/frontend serving
- [x] Comprehensive documentation

### 🔄 Phase 2 (Planned)
- [ ] Database for result storage  
- [ ] Batch analysis capabilities
- [ ] Performance optimizations
- [ ] User authentication and accounts

### 🚀 Phase 3 (Future)
- [ ] Real-time monitoring dashboard
- [ ] Network analysis for coordinated behavior
- [ ] ML model training on collected data
- [ ] Additional social media platforms

## 🤝 Contributing

This is a hackathon project with team members across different backgrounds and time zones. 

**Development Guidelines:**
- All code must include extensive comments
- Test changes thoroughly before committing: `pytest`
- Never commit API keys or credentials
- Follow the existing code structure
- Update documentation for new features
- Tests are located in `tests/` directory

**Getting Involved:**
1. Check with team leads (Andreas/Mitali) for task assignment
2. Create feature branch for new work
3. Test locally before submitting
4. Include documentation updates

## 📊 Example Analysis Output

```json
{
  "handle": "example.bsky.social",
  "overall_score": 0.75,
  "confidence": 0.85,
  "summary": "Analysis indicates this account is possibly a bot (risk level: HIGH, score: 0.75/1.00)",
  "follow_analysis": {
    "following_count": 2847,
    "follower_count": 12,
    "ratio": 237.25,
    "score": 0.8
  },
  "posting_pattern": {
    "posts_per_day_avg": 127.3,
    "unusual_frequency": true,
    "score": 0.9
  },
  "text_analysis": {
    "repetitive_content": true,
    "score": 0.7
  },
  "llm_analysis": {
    "model_used": "openai/gpt-4o-mini",
    "confidence": 0.85,
    "score": 0.6
  },
  "recommendations": [
    "⚠️ Suspicious follower/following patterns detected",
    "⚠️ Unusual posting patterns detected", 
    "🚫 Consider blocking or reporting this account"
  ]
}
```

## 📄 License

Developed for Apart Research hackathon. See individual team member agreements for specific licensing terms.

## 🆘 Support

- **Technical Issues**: Contact Andreas or Mitali
- **Policy Questions**: Contact Matt or Clare  
- **API Documentation**: See `/backend/README.md`
- **General Questions**: Check project documentation first

---

*Built with ❤️ for the fight against misinformation*