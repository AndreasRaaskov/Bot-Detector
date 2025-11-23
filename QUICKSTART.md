# Bot Detector - Quick Start Guide

This project now uses a **simple HTML/CSS/JavaScript frontend** with **zero Node.js dependencies**!

## Prerequisites

- Python 3.8+
- A virtual environment (recommended)
- Backend dependencies installed

## Quick Start

### Option 1: Development Mode (Recommended for Development)

Runs backend on port 8000 and frontend on port 8080:

```bash
./run_dev.sh
```

Then open your browser to:
- **Frontend:** http://localhost:8080
- **API:** http://localhost:8000
- **API Docs:** http://localhost:8000/docs

### Option 2: Production Mode (Single Port)

Serves both frontend and backend on port 8000:

```bash
./serve_prod.sh
```

Then open your browser to:
- **App:** http://localhost:8000
- **API Docs:** http://localhost:8000/docs

## Setup (First Time)

1. **Create and activate virtual environment:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Linux/Mac
   # or
   venv\Scripts\activate  # On Windows
   ```

2. **Install backend dependencies:**
   ```bash
   pip install -r backend/requirements.txt
   ```

3. **Configure your API keys:**
   - Copy `backend/config.json.example` to `backend/config.json`
   - Add your Bluesky and LLM API credentials

4. **Run the application:**
   ```bash
   ./run_dev.sh
   ```

## Project Structure

```
Bot-Detector/
├── backend/              # Python FastAPI backend
│   ├── main.py          # API server
│   ├── bot_detector.py  # Main detection logic
│   ├── analyzers.py     # Analysis methods
│   └── ...
├── frontend_simple/     # Simple HTML/CSS/JS frontend (NEW!)
│   ├── index.html      # Main page
│   ├── styles.css      # Styling
│   ├── app.js          # JavaScript logic
│   └── README.md       # Frontend documentation
├── run_dev.sh          # Development server script
└── serve_prod.sh       # Production server script
```

## What Changed?

### Before (Node.js-based frontend):
- Required Node.js, npm, and hundreds of dependencies
- Needed `npm install` and `npm run build`
- Used React, Vite, TailwindCSS, and many libraries
- Difficult to deploy on servers without Node.js

### Now (Simple frontend):
- **Zero Node.js dependencies**
- **No build process** - just HTML, CSS, and JavaScript
- **No npm install** needed
- **Easy to deploy** anywhere
- **Faster load times** and smaller file size
- **Same functionality** as before

## Deployment

### Local Server
Use `./serve_prod.sh` to run everything on one port.

### Remote Server
1. Copy the entire project to your server
2. Install Python dependencies
3. Configure your API keys
4. Run `./serve_prod.sh`
5. Optionally, use nginx or Apache as a reverse proxy

### Static Hosting + API Backend
You can host the `frontend_simple` directory on any static hosting service:
- GitHub Pages
- Netlify
- Vercel
- AWS S3
- Any web server

Just update `app.js` to point to your API backend URL.

## Troubleshooting

### Frontend can't connect to backend
- Make sure both servers are running
- Check that backend is on port 8000
- Check browser console for errors

### Port already in use
- Stop other services using ports 8000 or 8080
- Or change ports in the scripts

### API returns 404
- Make sure backend is running
- Check API endpoint in `frontend_simple/app.js`

## API Documentation

Once the backend is running, visit:
- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc

## Support

For issues or questions, check:
- `frontend_simple/README.md` - Frontend documentation
- `backend/README.md` - Backend documentation (if exists)
- Backend logs for error messages
