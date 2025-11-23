# Quick Production Deployment

## 🚀 Deploy in 5 Minutes

### Prerequisites
- Ubuntu/Debian server with root access
- Domain name pointed to your server
- Python 3.8+

### Step 1: Initial Setup

```bash
# Update system
sudo apt-get update && sudo apt-get upgrade -y

# Install dependencies
sudo apt-get install -y python3 python3-pip python3-venv nginx certbot python3-certbot-nginx git

# Create application directory
sudo mkdir -p /var/www/bot-detector
sudo chown $USER:$USER /var/www/bot-detector
```

### Step 2: Clone and Configure

```bash
# Clone repository (or upload files)
cd /var/www/bot-detector
git clone <your-repo> .

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r backend/requirements.txt

# Configure environment
cp .env.example .env
nano .env  # Edit with your credentials
```

### Step 3: Set Up nginx

```bash
# Copy nginx config
sudo cp deployment/nginx/bot-detector.conf /etc/nginx/sites-available/bot-detector

# Update domain in config
sudo nano /etc/nginx/sites-available/bot-detector
# Replace 'yourdomain.com' with your actual domain

# Enable site
sudo ln -s /etc/nginx/sites-available/bot-detector /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### Step 4: Get SSL Certificate

```bash
# Get Let's Encrypt certificate
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com

# Verify auto-renewal
sudo certbot renew --dry-run
```

### Step 5: Set Up Systemd Service

```bash
# Create log directory
sudo mkdir -p /var/log/bot-detector
sudo chown www-data:www-data /var/log/bot-detector

# Copy systemd service
sudo cp deployment/systemd/bot-detector.service /etc/systemd/system/

# Set correct ownership
sudo chown -R www-data:www-data /var/www/bot-detector

# Start service
sudo systemctl daemon-reload
sudo systemctl enable bot-detector
sudo systemctl start bot-detector

# Check status
sudo systemctl status bot-detector
```

### Step 6: Verify

```bash
# Check if service is running
curl https://yourdomain.com/health

# Test API
curl -X POST https://yourdomain.com/analyze \
  -H "Content-Type: application/json" \
  -d '{"bluesky_handle": "test.bsky.social"}'
```

## 🐳 Docker Deployment (Alternative)

Even faster with Docker:

```bash
# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Install Docker Compose
sudo apt-get install docker-compose-plugin

# Configure environment
cp .env.example .env
nano .env

# Start services
docker compose up -d

# View logs
docker compose logs -f

# Check health
curl http://localhost:8000/health
```

## 🔍 Monitoring

```bash
# View application logs
sudo journalctl -u bot-detector -f

# View nginx logs
sudo tail -f /var/log/nginx/bot-detector-error.log

# Check database
ls -lh /var/www/bot-detector/*.db
```

## 🛠️ Maintenance

### Update Application

```bash
cd /var/www/bot-detector
git pull
sudo systemctl restart bot-detector
```

### Backup Database

```bash
# Backup database
cp bot_detection.db "bot_detection_backup_$(date +%Y%m%d).db"

# Or set up automated backups
echo "0 2 * * * cp /var/www/bot-detector/bot_detection.db /var/www/bot-detector/backups/bot_detection_\$(date +\%Y\%m\%d).db" | crontab -
```

### View Statistics

```bash
# Check database size
du -h bot_detection.db

# Count analyzed users
sqlite3 bot_detection.db "SELECT COUNT(*) FROM users;"
```

## 🚨 Troubleshooting

### Service won't start
```bash
# Check logs
sudo journalctl -u bot-detector -n 50

# Check permissions
ls -la /var/www/bot-detector/

# Verify environment variables
sudo cat /var/www/bot-detector/.env
```

### Database locked
```bash
# Check if database is in use
lsof /var/www/bot-detector/bot_detection.db

# Restart service
sudo systemctl restart bot-detector
```

### HTTPS not working
```bash
# Test nginx config
sudo nginx -t

# Reload nginx
sudo systemctl reload nginx

# Check certificate
sudo certbot certificates
```

## 📊 Performance Tuning

### For High Traffic

1. **Enable caching in nginx**:
```nginx
proxy_cache_path /var/cache/nginx levels=1:2 keys_zone=api_cache:10m max_size=100m;

location /analyze {
    proxy_cache api_cache;
    proxy_cache_valid 200 1h;
    proxy_cache_key "$host$request_uri$request_body";
}
```

2. **Increase worker processes**:
```bash
# In /etc/systemd/system/bot-detector.service
[Service]
Environment="UVICORN_WORKERS=4"
```

3. **Use PostgreSQL** instead of SQLite for better concurrency

## 🔐 Security Hardening

```bash
# Set up firewall
sudo ufw allow 22
sudo ufw allow 80
sudo ufw allow 443
sudo ufw enable

# Disable root login
sudo nano /etc/ssh/sshd_config
# Set: PermitRootLogin no
sudo systemctl restart sshd

# Enable fail2ban
sudo apt-get install fail2ban
sudo systemctl enable fail2ban
```

## 📞 Need Help?

- Check logs: `sudo journalctl -u bot-detector -f`
- Test health: `curl https://yourdomain.com/health`
- nginx errors: `/var/log/nginx/error.log`
