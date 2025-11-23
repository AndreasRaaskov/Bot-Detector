# Bot Detector - Simple Frontend

This is a plain HTML/CSS/JavaScript version of the Bot Detector frontend with **zero Node.js dependencies**.

## Features

- Pure HTML, CSS, and JavaScript (no build process required)
- Works with any web server
- Compatible with all modern desktop browsers
- Clean, functional design
- All the same functionality as the React version

## How to Use

### Option 1: Use the Deployment Scripts (Easiest!)

**Development Mode** (frontend on 8080, backend on 8000):
```bash
cd ..  # Go to project root
./run_dev.sh
```

**Production Mode** (everything on 8000):
```bash
cd ..  # Go to project root
./serve_prod.sh
```

See `../QUICKSTART.md` for more details!

### Option 2: Manual Setup with Backend

The backend is configured to serve static files from `frontend/dist`. The `serve_prod.sh` script automatically copies files there.

### Option 3: Use a Simple HTTP Server

If you just want to test the frontend:

```bash
cd frontend_simple
python3 -m http.server 8080
```

Then open your browser to `http://localhost:8080`

**Note:** If using a separate server, make sure to update the API_BASE_URL in `app.js` to point to your backend (default is `http://localhost:8000`)

### Option 3: Open Directly (Limited)

You can open `index.html` directly in your browser, but you'll need to:
1. Run the backend on the same domain/port or
2. Enable CORS on your backend (already enabled)
3. Update the `API_BASE_URL` in `app.js` to your backend URL

## Files

- `index.html` - Main HTML structure
- `styles.css` - All styling (plain CSS, no preprocessors)
- `app.js` - Application logic (vanilla JavaScript)
- `README.md` - This file

## API Configuration

The frontend expects the backend API at the same origin by default. To change this, edit `app.js`:

```javascript
const API_BASE_URL = 'http://your-backend-url:port';
```

## Browser Compatibility

Works on all modern desktop browsers:
- Chrome/Edge 90+
- Firefox 88+
- Safari 14+

## Differences from React Version

This version:
- ✅ No build process needed
- ✅ No package.json or node_modules
- ✅ Much smaller file size
- ✅ Faster load times
- ✅ Easier to deploy
- ❌ No mobile optimization (as requested)
- ❌ Simpler animations
- ❌ No fancy UI component libraries

## License

Same as the main Bot Detector project.
