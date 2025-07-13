import os
import sys
import time
import uuid
import json
import random
import logging
import asyncio
import argparse
from typing import Dict, Set
from quart import Quart, request, jsonify, websocket, send_from_directory
from quart_cors import cors

# Mock browser automation for demo purposes
class MockBrowser:
    def __init__(self, index):
        self.index = index
    
    async def new_context(self, **kwargs):
        return MockContext()
    
    async def close(self):
        pass

class MockContext:
    async def new_page(self):
        return MockPage()
    
    async def close(self):
        pass

class MockPage:
    async def route(self, url, handler):
        pass
    
    async def goto(self, url):
        pass
    
    async def eval_on_selector(self, selector, script):
        pass
    
    async def input_value(self, selector, timeout=None):
        # Simulate solving captcha
        await asyncio.sleep(random.uniform(2, 5))
        return "mock_captcha_token_" + str(uuid.uuid4())[:8]
    
    async def locator(self, selector):
        return MockLocator()

class MockLocator:
    async def click(self, timeout=None):
        pass


COLORS = {
    'MAGENTA': '\033[35m',
    'BLUE': '\033[34m',
    'GREEN': '\033[32m',
    'YELLOW': '\033[33m',
    'RED': '\033[31m',
    'RESET': '\033[0m',
}


class CustomLogger(logging.Logger):
    @staticmethod
    def format_message(level, color, message):
        timestamp = time.strftime('%H:%M:%S')
        return f"[{timestamp}] [{COLORS.get(color)}{level}{COLORS.get('RESET')}] -> {message}"

    def debug(self, message, *args, **kwargs):
        super().debug(self.format_message('DEBUG', 'MAGENTA', message), *args, **kwargs)

    def info(self, message, *args, **kwargs):
        super().info(self.format_message('INFO', 'BLUE', message), *args, **kwargs)

    def success(self, message, *args, **kwargs):
        super().info(self.format_message('SUCCESS', 'GREEN', message), *args, **kwargs)

    def warning(self, message, *args, **kwargs):
        super().warning(self.format_message('WARNING', 'YELLOW', message), *args, **kwargs)

    def error(self, message, *args, **kwargs):
        super().error(self.format_message('ERROR', 'RED', message), *args, **kwargs)


logging.setLoggerClass(CustomLogger)
logger = logging.getLogger("TurnstileWebApp")
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler(sys.stdout)
logger.addHandler(handler)


class WebSocketManager:
    def __init__(self):
        self.connections: Set[object] = set()
    
    async def add_connection(self, websocket):
        self.connections.add(websocket)
        logger.info(f"WebSocket connection added. Total: {len(self.connections)}")
    
    async def remove_connection(self, websocket):
        self.connections.discard(websocket)
        logger.info(f"WebSocket connection removed. Total: {len(self.connections)}")
    
    async def broadcast(self, message_type: str, data: dict):
        if not self.connections:
            return
        
        message = json.dumps({"type": message_type, "data": data})
        disconnected = set()
        
        for ws in self.connections:
            try:
                await ws.send(message)
            except Exception as e:
                logger.warning(f"Failed to send message to WebSocket: {e}")
                disconnected.add(ws)
        
        # Remove disconnected connections
        for ws in disconnected:
            self.connections.discard(ws)


class TurnstileWebApp:
    HTML_TEMPLATE = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Turnstile Solver</title>
        <script src="https://challenges.cloudflare.com/turnstile/v0/api.js" async></script>
        <script>
            async function fetchIP() {
                try {
                    const response = await fetch('https://api64.ipify.org?format=json');
                    const data = await response.json();
                    document.getElementById('ip-display').innerText = `Your IP: ${data.ip}`;
                } catch (error) {
                    console.error('Error fetching IP:', error);
                    document.getElementById('ip-display').innerText = 'Failed to fetch IP';
                }
            }
            window.onload = fetchIP;
        </script>
    </head>
    <body>
        <!-- cf turnstile -->
        <p id="ip-display">Fetching your IP...</p>
    </body>
    </html>
    """

    def __init__(self, headless: bool, useragent: str, debug: bool, browser_type: str, thread: int, proxy_support: bool):
        self.app = Quart(__name__)
        self.app = cors(self.app, allow_origin="*")
        self.debug = debug
        self.results = self._load_results()
        self.browser_type = browser_type
        self.headless = headless
        self.useragent = useragent
        self.thread_count = thread
        self.proxy_support = proxy_support
        self.browser_pool = asyncio.Queue()
        self.browser_args = []
        self.ws_manager = WebSocketManager()
        self.session_data = {}  # Store session context
        
        if useragent:
            self.browser_args.append(f"--user-agent={useragent}")

        self._setup_routes()

    @staticmethod
    def _load_results():
        """Load previous results from results.json."""
        try:
            if os.path.exists("results.json"):
                with open("results.json", "r") as f:
                    return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            logger.warning(f"Error loading results: {str(e)}. Starting with an empty results dictionary.")
        return {}

    def _save_results(self):
        """Save results to results.json."""
        try:
            with open("results.json", "w") as result_file:
                json.dump(self.results, result_file, indent=4)
        except IOError as e:
            logger.error(f"Error saving results to file: {str(e)}")

    def _setup_routes(self) -> None:
        """Set up the application routes."""
        self.app.before_serving(self._startup)
        self.app.route('/turnstile', methods=['GET'])(self.process_turnstile)
        self.app.route('/result', methods=['GET'])(self.get_result)
        self.app.route('/')(self.index)
        self.app.route('/dashboard')(self.dashboard)
        self.app.route('/static/<path:filename>')(self.static_files)
        self.app.websocket('/ws')(self.websocket_handler)

    async def _startup(self) -> None:
        """Initialize the browser and page pool on startup."""
        logger.info("Starting browser initialization")
        try:
            await self._initialize_browser()
        except Exception as e:
            logger.error(f"Failed to initialize browser: {str(e)}")
            raise

    async def _initialize_browser(self) -> None:
        """Initialize the browser and create the page pool."""
        logger.warning("Using mock browser for demonstration purposes")
        
        for i in range(self.thread_count):
            browser = MockBrowser(i + 1)
            await self.browser_pool.put((i+1, browser))

            if self.debug:
                logger.success(f"Mock Browser {i + 1} initialized successfully")

        logger.success(f"Mock browser pool initialized with {self.browser_pool.qsize()} browsers")

    async def websocket_handler(self):
        """Handle WebSocket connections."""
        await self.ws_manager.add_connection(websocket)
        
        try:
            while True:
                try:
                    message = await websocket.receive()
                    data = json.loads(message)
                    await self.handle_websocket_message(websocket, data)
                except Exception as e:
                    logger.error(f"WebSocket message error: {e}")
                    break
        except Exception as e:
            logger.error(f"WebSocket connection error: {e}")
        finally:
            await self.ws_manager.remove_connection(websocket)

    async def handle_websocket_message(self, ws, data):
        """Handle incoming WebSocket messages."""
        message_type = data.get('type')
        message_data = data.get('data', {})
        
        if message_type == 'ping':
            await ws.send(json.dumps({"type": "pong", "data": {"timestamp": time.time()}}))
        elif message_type == 'get_stats':
            stats = {
                "queue_size": self.browser_pool.qsize(),
                "total_tasks": len(self.results),
                "active_connections": len(self.ws_manager.connections)
            }
            await ws.send(json.dumps({"type": "server_stats", "data": stats}))

    async def _solve_turnstile(self, task_id: str, url: str, sitekey: str, action: str = None, cdata: str = None):
        """Solve the Turnstile challenge with WebSocket updates."""
        
        # Notify WebSocket clients
        await self.ws_manager.broadcast("task_created", {"taskId": task_id})
        
        index, browser = await self.browser_pool.get()
        context = await browser.new_context()
        page = await context.new_page()
        start_time = time.time()

        try:
            if self.debug:
                logger.debug(f"Mock Browser {index}: Starting Turnstile solve for URL: {url} with Sitekey: {sitekey}")
                await self.ws_manager.broadcast("task_progress", {
                    "taskId": task_id, 
                    "status": f"Mock Browser {index}: Starting solve process"
                })

            url_with_slash = url + "/" if not url.endswith("/") else url
            turnstile_div = f'<div class="cf-turnstile" style="background: white;" data-sitekey="{sitekey}"' + (f' data-action="{action}"' if action else '') + (f' data-cdata="{cdata}"' if cdata else '') + '></div>'
            page_data = self.HTML_TEMPLATE.replace("<!-- cf turnstile -->", turnstile_div)

            await page.route(url_with_slash, lambda route: route.fulfill(body=page_data, status=200))
            await page.goto(url_with_slash)

            if self.debug:
                await self.ws_manager.broadcast("task_progress", {
                    "taskId": task_id, 
                    "status": f"Mock Browser {index}: Setting up Turnstile widget"
                })

            await page.eval_on_selector("//div[@class='cf-turnstile']", "el => el.style.width = '70px'")

            for attempt in range(3):  # Reduced attempts for demo
                try:
                    await self.ws_manager.broadcast("task_progress", {
                        "taskId": task_id, 
                        "status": f"Mock Browser {index}: Solving attempt {attempt + 1}/3"
                    })
                    
                    turnstile_check = await page.input_value("[name=cf-turnstile-response]", timeout=2000)
                    if turnstile_check:
                        elapsed_time = round(time.time() - start_time, 3)
                        logger.success(f"Mock Browser {index}: Successfully solved captcha in {elapsed_time} seconds")

                        self.results[task_id] = {"value": turnstile_check, "elapsed_time": elapsed_time}
                        self._save_results()
                        
                        await self.ws_manager.broadcast("task_completed", {
                            "taskId": task_id,
                            "result": turnstile_check,
                            "elapsed_time": elapsed_time
                        })
                        break
                except Exception as e:
                    if self.debug:
                        logger.debug(f"Mock Browser {index}: Attempt {attempt + 1} failed: {str(e)}")

            if self.results.get(task_id) == "CAPTCHA_NOT_READY":
                elapsed_time = round(time.time() - start_time, 3)
                self.results[task_id] = {"value": "CAPTCHA_FAIL", "elapsed_time": elapsed_time}
                
                await self.ws_manager.broadcast("task_failed", {
                    "taskId": task_id,
                    "error": "Failed to solve captcha after 3 attempts"
                })
                
                if self.debug:
                    logger.error(f"Mock Browser {index}: Error solving Turnstile in {elapsed_time} seconds")
                    
        except Exception as e:
            elapsed_time = round(time.time() - start_time, 3)
            self.results[task_id] = {"value": "CAPTCHA_FAIL", "elapsed_time": elapsed_time}
            
            await self.ws_manager.broadcast("task_failed", {
                "taskId": task_id,
                "error": str(e)
            })
            
            if self.debug:
                logger.error(f"Mock Browser {index}: Error solving Turnstile: {str(e)}")
        finally:
            if self.debug:
                logger.debug(f"Mock Browser {index}: Clearing page state")

            await context.close()
            await self.browser_pool.put((index, browser))

    async def process_turnstile(self):
        """Handle the /turnstile endpoint requests."""
        url = request.args.get('url')
        sitekey = request.args.get('sitekey')
        action = request.args.get('action')
        cdata = request.args.get('cdata')

        if not url or not sitekey:
            return jsonify({
                "status": "error",
                "error": "Both 'url' and 'sitekey' are required"
            }), 400

        task_id = str(uuid.uuid4())
        self.results[task_id] = "CAPTCHA_NOT_READY"
        
        # Store session context
        self.session_data[task_id] = {
            "url": url,
            "sitekey": sitekey,
            "action": action,
            "cdata": cdata,
            "created_at": time.time()
        }

        try:
            asyncio.create_task(self._solve_turnstile(task_id=task_id, url=url, sitekey=sitekey, action=action, cdata=cdata))

            if self.debug:
                logger.debug(f"Request completed with taskid {task_id}.")
            return jsonify({"task_id": task_id}), 202
        except Exception as e:
            logger.error(f"Unexpected error processing request: {str(e)}")
            return jsonify({
                "status": "error",
                "error": str(e)
            }), 500

    async def get_result(self):
        """Return solved data"""
        task_id = request.args.get('id')

        if not task_id or task_id not in self.results:
            return jsonify({"status": "error", "error": "Invalid task ID/Request parameter"}), 400

        result = self.results[task_id]
        status_code = 200

        if isinstance(result, dict) and "CAPTCHA_FAIL" in result.get("value", ""):
            status_code = 422

        return result, status_code

    async def static_files(self, filename):
        """Serve static files."""
        return await send_from_directory('static', filename)

    async def dashboard(self):
        """Serve the dashboard page."""
        return await send_from_directory('static', 'index.html')

    @staticmethod
    async def index():
        """Serve the API documentation page."""
        return """
            <!DOCTYPE html>
            <html lang="en">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>Turnstile Solver API</title>
                <script src="https://cdn.tailwindcss.com"></script>
            </head>
            <body class="bg-gray-900 text-gray-200 min-h-screen flex items-center justify-center">
                <div class="bg-gray-800 p-8 rounded-lg shadow-md max-w-2xl w-full border border-red-500">
                    <h1 class="text-3xl font-bold mb-6 text-center text-red-500">Turnstile Solver API</h1>

                    <div class="mb-6 text-center">
                        <a href="/dashboard" class="bg-blue-600 hover:bg-blue-700 text-white font-bold py-3 px-6 rounded-lg transition-colors">
                            Open Dashboard
                        </a>
                    </div>

                    <p class="mb-4 text-gray-300">To use the turnstile service, send a GET request to 
                       <code class="bg-red-700 text-white px-2 py-1 rounded">/turnstile</code> with the following query parameters:</p>

                    <ul class="list-disc pl-6 mb-6 text-gray-300">
                        <li><strong>url</strong>: The URL where Turnstile is to be validated</li>
                        <li><strong>sitekey</strong>: The site key for Turnstile</li>
                        <li><strong>action</strong> (optional): Action parameter for Turnstile</li>
                        <li><strong>cdata</strong> (optional): Custom data for Turnstile</li>
                    </ul>

                    <div class="bg-gray-700 p-4 rounded-lg mb-6 border border-red-500">
                        <p class="font-semibold mb-2 text-red-400">Example usage:</p>
                        <code class="text-sm break-all text-red-300">/turnstile?url=https://example.com&sitekey=sitekey</code>
                    </div>

                    <div class="bg-blue-900 border-l-4 border-blue-600 p-4 mb-6">
                        <p class="text-blue-200 font-semibold">Features:</p>
                        <ul class="text-blue-200 text-sm mt-2 list-disc pl-4">
                            <li>Real-time WebSocket updates</li>
                            <li>Modern web dashboard</li>
                            <li>Session persistence</li>
                            <li>Automatic reconnection</li>
                            <li>Docker deployment ready</li>
                        </ul>
                    </div>

                    <div class="bg-yellow-900 border-l-4 border-yellow-600 p-4 mb-6">
                        <p class="text-yellow-200 font-semibold">Demo Mode:</p>
                        <p class="text-yellow-200 text-sm mt-2">This instance is running in demo mode with mock browser automation. Install patchright or camoufox for full functionality.</p>
                    </div>

                    <div class="bg-red-900 border-l-4 border-red-600 p-4 mb-6">
                        <p class="text-red-200 font-semibold">This project is inspired by 
                           <a href="https://github.com/Body-Alhoha/turnaround" class="text-red-300 hover:underline">Turnaround</a> 
                           and is currently maintained by 
                           <a href="https://github.com/Theyka" class="text-red-300 hover:underline">Theyka</a> 
                           and <a href="https://github.com/sexfrance" class="text-red-300 hover:underline">Sexfrance</a>.</p>
                    </div>
                </div>
            </body>
            </html>
        """


def parse_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description="Turnstile Web Application")

    parser.add_argument('--headless', type=bool, default=False, help='Run the browser in headless mode (default: False)')
    parser.add_argument('--useragent', type=str, default=None, help='Specify a custom User-Agent string')
    parser.add_argument('--debug', type=bool, default=False, help='Enable debug mode (default: False)')
    parser.add_argument('--browser_type', type=str, default='chromium', help='Browser type: chromium, chrome, msedge, camoufox (default: chromium)')
    parser.add_argument('--thread', type=int, default=1, help='Number of browser threads (default: 1)')
    parser.add_argument('--proxy', type=bool, default=False, help='Enable proxy support (default: False)')
    parser.add_argument('--host', type=str, default='0.0.0.0', help='Host IP address (default: 0.0.0.0)')
    parser.add_argument('--port', type=str, default='8401', help='Port number (default: 8401)')
    return parser.parse_args()


def create_app(headless: bool, useragent: str, debug: bool, browser_type: str, thread: int, proxy_support: bool) -> Quart:
    server = TurnstileWebApp(headless=headless, useragent=useragent, debug=debug, browser_type=browser_type, thread=thread, proxy_support=proxy_support)
    return server.app


if __name__ == '__main__':
    args = parse_args()
    
    logger.info(f"Starting Turnstile Web Application on {COLORS.get('GREEN')}http://{args.host}:{args.port}{COLORS.get('RESET')}")
    logger.info(f"Dashboard available at {COLORS.get('BLUE')}http://{args.host}:{args.port}/dashboard{COLORS.get('RESET')}")
    
    app = create_app(
        headless=args.headless, 
        debug=args.debug, 
        useragent=args.useragent, 
        browser_type=args.browser_type, 
        thread=args.thread, 
        proxy_support=args.proxy
    )
    app.run(host=args.host, port=int(args.port))