# Turnstile Solver Web Application

A modern, user-friendly web application for solving Cloudflare Turnstile challenges with real-time updates, session persistence, and Docker deployment support.

## Features

✅ **Modern Web Interface**
- Responsive dashboard with real-time status updates
- Interactive task management and history
- Beautiful gradient UI with glass-morphism effects
- Mobile-friendly design

✅ **Real-time Communication**
- WebSocket support for live updates
- Automatic reconnection with exponential backoff
- Real-time progress tracking for each challenge

✅ **Session Persistence**
- Context management for ongoing tasks
- Local storage for form data and task history
- Session recovery after disconnection

✅ **User-friendly Features**
- Intuitive error handling with notifications
- Export functionality for results
- Task filtering and search
- Copy-to-clipboard for tokens

✅ **Docker Deployment**
- Production-ready Docker configuration
- Port 8401 exposure
- Environment variable configuration
- Health checks included

## Quick Start

### Option 1: Direct Python Execution
```bash
# Install dependencies
pip install quart quart-cors hypercorn

# Run the web application
python web_app_demo.py --debug true --port 8401 --host 0.0.0.0

# Access the dashboard
# http://localhost:8401/dashboard
```

### Option 2: Using Main Application
```bash
# Run with integrated main.py
python main.py
# Select option 4 (Web Application)
```

### Option 3: Docker Deployment
```bash
# Build and run with Docker Compose
docker-compose up --build

# Or build manually
docker build -f Docker/Dockerfile -t turnstile-web .
docker run -p 8401:8401 -e RUN_WEB_APP=true turnstile-web
```

## Usage

1. **Access the Dashboard**: Navigate to `http://localhost:8401/dashboard`
2. **Enter Turnstile Details**: 
   - Target URL where Turnstile needs to be solved
   - Site Key from the target website
   - Optional: Action and CData parameters
3. **Start Solving**: Click "Solve Challenge" to begin
4. **Monitor Progress**: Watch real-time updates in the task history
5. **Get Results**: Copy the solved token when complete

## API Endpoints

- `GET /` - API documentation
- `GET /dashboard` - Web dashboard interface
- `GET /turnstile?url=<url>&sitekey=<key>` - Start solving task
- `GET /result?id=<task_id>` - Get task result
- `WebSocket /ws` - Real-time updates

## Configuration

### Command Line Arguments
```bash
--host         Host IP address (default: 0.0.0.0)
--port         Port number (default: 8401)
--debug        Enable debug mode (default: False)
--headless     Run browser in headless mode (default: False)
--browser_type Browser type: chromium, chrome, msedge, camoufox
--thread       Number of browser threads (default: 1)
--proxy        Enable proxy support (default: False)
--useragent    Custom User-Agent string
```

### Environment Variables (Docker)
```bash
RUN_WEB_APP=true    # Enable web application mode
TZ=America/New_York # Set timezone
```

## File Structure

```
├── web_app.py              # Full web application (requires browser libs)
├── web_app_demo.py         # Demo version with mock browser
├── main.py                 # Updated main entry point
├── static/
│   ├── index.html          # Dashboard interface
│   └── script.js           # Frontend JavaScript
├── Docker/
│   ├── Dockerfile          # Docker configuration
│   └── run.sh              # Docker startup script
├── docker-compose.yml      # Docker Compose configuration
└── requirements.txt        # Python dependencies
```

## Browser Dependencies

For full functionality, install one of:
- `patchright` - Playwright fork with enhanced features
- `camoufox[geoip]` - Privacy-focused browser automation

Demo mode uses mock browser automation for testing without dependencies.

## Production Deployment

1. **Install Dependencies**: `pip install -r requirements.txt`
2. **Configure Environment**: Set appropriate host, port, and security settings
3. **Use ASGI Server**: Deploy with Hypercorn or Uvicorn for production
4. **Setup Reverse Proxy**: Use Nginx or Apache for SSL termination
5. **Monitor Health**: Use the built-in health check endpoint

## Security Notes

- Default binding to `0.0.0.0` allows external access
- Use firewall rules to restrict access in production
- Consider SSL/TLS termination with reverse proxy
- Monitor resource usage with multiple browser threads

## Browser Compatibility

- Chrome/Chromium (Recommended)
- Microsoft Edge
- Camoufox (Privacy-focused)
- Supports both headful and headless modes

## Troubleshooting

1. **Port Already in Use**: Change port with `--port <number>`
2. **Browser Not Found**: Install patchright or camoufox
3. **WebSocket Issues**: Check firewall and proxy settings
4. **Memory Usage**: Reduce thread count with `--thread 1`

## Development

The application is built with:
- **Backend**: Quart (async Flask) + WebSockets
- **Frontend**: Vanilla JavaScript + Tailwind CSS
- **Browser Automation**: Playwright/Camoufox
- **Deployment**: Docker + Hypercorn ASGI server

## License

This project is inspired by [Turnaround](https://github.com/Body-Alhoha/turnaround) and is maintained by [Theyka](https://github.com/Theyka) and [Sexfrance](https://github.com/sexfrance).