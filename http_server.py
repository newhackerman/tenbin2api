#!/usr/bin/env python3
import http.server
import socketserver
import sys

PORT = 8402

class MyHandler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        super().end_headers()

def main():
    try:
        with socketserver.TCPServer(("", PORT), MyHandler) as httpd:
            print(f"HTTP服务器启动在 http://localhost:{PORT}")
            print(f"请访问: http://localhost:{PORT}/chat.html")
            httpd.serve_forever()
    except OSError as e:
        print(f"端口 {PORT} 被占用: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n服务器已停止")

if __name__ == "__main__":
    main()