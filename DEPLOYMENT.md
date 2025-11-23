# Production Deployment Guide

This guide covers deploying the Bot Detector application to production with proper security, HTTPS, and scalability.

## 🔒 Security Checklist

Before deploying to production, ensure you have:

- [ ] **HTTPS/SSL Certificate** - Never run in production without HTTPS
- [ ] **Environment Variables** - All secrets in env vars, not config files
- [ ] **CORS Configuration** - Restrict allowed origins
- [ ] **Rate Limiting** - Prevent abuse
- [ ] **API Authentication** - Optional but recommended
- [ ] **Database Security** - Proper file permissions
- [ ] **Error Handling** - Don't expose stack traces
- [ ] **Logging** - Proper logging without sensitive data
- [ ] **Health Checks** - Monitor service health
- [ ] **Firewall Rules** - Restrict incoming/outgoing traffic

## 📋 Prerequisites

1. **Server/Lambda Environment** with Python 3.8+
2. **Domain name** with DNS configured
3. **SSL Certificate** (Let's Encrypt recommended)
4. **Reverse proxy** (nginx, Caddy, or API Gateway)
5. **Bluesky API credentials**
6. **LLM API keys** (optional)

## 🚀 Deployment Options

### Option 1: AWS Lambda + API Gateway (Serverless)

**Note:** The current implementation uses SQLite which doesn't work well with Lambda. You'll need to:
- Use AWS RDS or DynamoDB instead of SQLite
- Or use ECS/EC2 instead of Lambda

See `deployment/aws-lambda/` for configuration.

### Option 2: Traditional Server (Recommended)

Deploy on a VPS, EC2, or container platform.

#### Quick Start with Docker

```bash
# Build and run with Docker
docker-compose up -d
```

#### Manual Deployment

```bash
# 1. Set up environment
python3 -m venv venv
source venv/bin/activate
pip install -r backend/requirements.txt

# 2. Configure environment variables
cp .env.example .env
# Edit .env with your secrets

# 3. Set up reverse proxy (nginx example below)
sudo cp deployment/nginx/bot-detector.conf /etc/nginx/sites-available/
sudo ln -s /etc/nginx/sites-available/bot-detector.conf /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx

# 4. Set up systemd service
sudo cp deployment/systemd/bot-detector.service /etc/systemd/system/
sudo systemctl enable bot-detector
sudo systemctl start bot-detector

# 5. Get SSL certificate
sudo certbot --nginx -d yourdomain.com
```

## 🔐 HTTPS Setup

### Using Let's Encrypt (Recommended)

```bash
# Install certbot
sudo apt-get install certbot python3-certbot-nginx

# Get certificate
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com

# Auto-renewal is configured automatically
```

### Using Custom Certificate

Place your certificates:
- Certificate: `/etc/ssl/certs/bot-detector.crt`
- Private key: `/etc/ssl/private/bot-detector.key`

Update nginx configuration accordingly.

## 🛡️ Security Hardening

### 1. Environment Variables

**Never commit secrets!** Use environment variables:

```bash
# .env (DO NOT COMMIT THIS FILE)
BLUESKY_USERNAME=your-bot-username
BLUESKY_PASSWORD=your-bot-password
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
GOOGLE_API_KEY=...

# Production settings
DEBUG_MODE=false
ALLOWED_ORIGINS=https://yourdomain.com
API_HOST=127.0.0.1
API_PORT=8000
```

### 2. CORS Configuration

Update `backend/main.py`:

```python
# Production CORS - RESTRICT ORIGINS!
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://yourdomain.com",
        "https://www.yourdomain.com"
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
)
```

### 3. Rate Limiting

Add to `backend/main.py`:

```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

@app.post("/analyze")
@limiter.limit("10/minute")  # Max 10 requests per minute
async def analyze_user(request: Request, analysis_request: UserAnalysisRequest):
    # ... existing code
```

Install: `pip install slowapi`

### 4. API Authentication (Optional)

Add API key authentication:

```python
from fastapi import Header, HTTPException

async def verify_api_key(x_api_key: str = Header(...)):
    if x_api_key != os.getenv("API_KEY"):
        raise HTTPException(status_code=403, detail="Invalid API key")
    return x_api_key

@app.post("/analyze", dependencies=[Depends(verify_api_key)])
async def analyze_user(analysis_request: UserAnalysisRequest):
    # ... existing code
```

### 5. Database Security

```bash
# Set proper permissions on database
chmod 600 bot_detection.db
chown www-data:www-data bot_detection.db  # Or your app user
```

## 📊 Monitoring & Logging

### Health Check Endpoint

Already configured at `/health`:

```bash
curl https://yourdomain.com/health
```

### Logging Configuration

Update logging in production:

```python
import logging

if not DEBUG_MODE:
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('/var/log/bot-detector/app.log'),
            logging.StreamHandler()
        ]
    )
```

### Monitoring Services

Consider using:
- **Uptime monitoring**: UptimeRobot, Pingdom
- **Error tracking**: Sentry
- **Logs**: CloudWatch, Datadog, Logtail
- **Metrics**: Prometheus + Grafana

## 🐳 Docker Deployment

See `docker-compose.yml` for containerized deployment:

```yaml
services:
  backend:
    build: .
    environment:
      - BLUESKY_USERNAME=${BLUESKY_USERNAME}
      - BLUESKY_PASSWORD=${BLUESKY_PASSWORD}
      # ... other env vars
    volumes:
      - ./bot_detection.db:/app/bot_detection.db
    restart: unless-stopped
```

## 🔄 Continuous Deployment

### GitHub Actions Example

```yaml
name: Deploy

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Deploy to server
        run: |
          ssh user@server 'cd /var/www/bot-detector && git pull && systemctl restart bot-detector'
```

## 📈 Scaling Considerations

### Database

- **SQLite**: Good for < 1000 requests/day
- **PostgreSQL**: Better for production (needs code changes)
- **Cache layer**: Redis for frequent queries

### Application

- **Load balancer**: nginx or HAProxy
- **Multiple instances**: Run behind load balancer
- **Auto-scaling**: Use cloud auto-scaling groups

### CDN

Serve frontend through CDN:
- Cloudflare
- AWS CloudFront
- Fastly

## 🆘 Troubleshooting

### HTTPS not working
```bash
# Check nginx config
sudo nginx -t

# Check certificate
sudo certbot certificates

# Check firewall
sudo ufw status
sudo ufw allow 443
```

### Permission errors
```bash
# Fix file permissions
sudo chown -R www-data:www-data /var/www/bot-detector
sudo chmod -R 755 /var/www/bot-detector
sudo chmod 600 /var/www/bot-detector/bot_detection.db
```

### Database locked
```bash
# Check if database is being used
lsof bot_detection.db

# Restart service
sudo systemctl restart bot-detector
```

## 📝 Environment Variables Reference

| Variable | Required | Description | Example |
|----------|----------|-------------|---------|
| `BLUESKY_USERNAME` | Yes | Bluesky bot account | `bot.bsky.social` |
| `BLUESKY_PASSWORD` | Yes | Bluesky password | `****` |
| `OPENAI_API_KEY` | No | OpenAI API key | `sk-...` |
| `ANTHROPIC_API_KEY` | No | Anthropic API key | `sk-ant-...` |
| `GOOGLE_API_KEY` | No | Google AI key | `AI...` |
| `DEBUG_MODE` | No | Enable debug mode | `false` |
| `API_HOST` | No | Host to bind to | `127.0.0.1` |
| `API_PORT` | No | Port to bind to | `8000` |
| `DATABASE_PATH` | No | SQLite DB path | `bot_detection.db` |

## 🎯 Production Checklist

Before going live:

- [ ] All secrets in environment variables
- [ ] CORS restricted to your domain
- [ ] Rate limiting enabled
- [ ] HTTPS configured and working
- [ ] Health check endpoint responding
- [ ] Logging configured
- [ ] Monitoring set up
- [ ] Backups configured for database
- [ ] Error pages customized
- [ ] Performance tested
- [ ] Security audit completed
- [ ] Documentation updated
- [ ] Team knows how to deploy/rollback

## 📞 Support

For deployment issues, check:
- Logs: `sudo journalctl -u bot-detector -f`
- nginx logs: `/var/log/nginx/error.log`
- Application logs: `/var/log/bot-detector/app.log`
