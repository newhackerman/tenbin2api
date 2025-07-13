#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Simple HTTP server to serve the chat HTML file
"""

import http.server
import socketserver
import webbrowser
import threading
import time

PORT = 8402

class MyHandler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        # 添加CORS头解决跨域问题
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        super().end_headers()

def start_server():
    with socketserver.TCPServer(("", PORT), MyHandler) as httpd:
        print(f"HTTP服务器启动在 http://localhost:{PORT}")
        print(f"请访问: http://localhost:{PORT}/chat.html")
        httpd.serve_forever()

def open_browser():
    time.sleep(1)  # 等待服务器启动
    webbrowser.open(f'http://localhost:{PORT}/chat.html')

if __name__ == "__main__":
    # 启动浏览器
    browser_thread = threading.Thread(target=open_browser)
    browser_thread.daemon = True
    browser_thread.start()
    
    # 启动服务器
    try:
        start_server()
    except KeyboardInterrupt:
        print("\n服务器已停止")