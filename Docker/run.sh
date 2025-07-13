#!/bin/bash

start_web_app() {
    echo "Starting Turnstile Web Application..."
    cd /app
    python3 web_app.py --browser_type chrome --host 0.0.0.0 --port 8401 --headless true --useragent "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
}

stop_services() {
    echo "Stopping services..."
    exit 0
}

if [ -n "$TZ" ]; then
    ln -snf /usr/share/zoneinfo/$TZ /etc/localtime
    echo $TZ >/etc/timezone
fi

trap "stop_services" SIGKILL SIGTERM SIGHUP SIGINT EXIT

if [ "$RUN_WEB_APP" = "true" ]; then
    echo "Starting Web Application in headless mode on port 8401..."
    xvfb-run -a start_web_app
else
    echo "Web application not configured to start. Set RUN_WEB_APP=true to enable."
    tail -f /dev/null
fi
