# Continuum Frontend

A modern, responsive frontend for the Continuum AI Agent System.

## Features

- 🎨 Beautiful UI with custom color palette
- 📊 Real-time progress tracking
- 📈 API call statistics
- ⏱️ Execution time display
- 📝 Results visualization
- 📚 History of previous runs
- 📱 Fully responsive design

## Setup

1. Make sure your FastAPI backend is running on `http://127.0.0.1:8000`

2. Open `index.html` in a web browser, or serve it using a local server:

```bash
# Using Python
cd frontend
python -m http.server 8080

# Using Node.js (if you have http-server installed)
npx http-server -p 8080
```

3. Open `http://localhost:8080` in your browser

## Configuration

If your backend is running on a different URL, update the `API_BASE_URL` in `app.js`:

```javascript
const API_BASE_URL = 'http://your-backend-url:port';
```

## Color Palette

The frontend uses the following color scheme:

- **Primary**: #4F46E5 (Indigo)
- **Secondary**: #22D3EE (Cyan)
- **Accent**: #A5B4FC (Soft Indigo)
- **Background**: #0F172A (Dark Navy)
- **Card Background**: #111827
- **Success**: #22C55E
- **Warning**: #FACC15
- **Error**: #EF4444

## Browser Support

- Chrome/Edge (latest)
- Firefox (latest)
- Safari (latest)

## Notes

- The frontend currently shows final results after execution completes
- For real-time progress updates, WebSocket support would need to be added to the backend
- CORS may need to be enabled on the FastAPI backend if serving from a different origin

