#!/usr/bin/env python3
"""
BytePlus API Proxy Server
ブラウザからのCORS制限を回避するためのプロキシサーバー
"""

from http.server import HTTPServer, BaseHTTPRequestHandler
import json
import urllib.request
import urllib.error
import ssl

class ProxyHandler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        """プリフライトリクエスト処理"""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        self.end_headers()

    def do_POST(self):
        """POST リクエスト処理"""
        if self.path == '/api/proxy':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)

            try:
                # リクエストデータをパース
                data = json.loads(post_data.decode('utf-8'))
                api_key = data.get('apiKey')
                endpoint = data.get('endpoint')
                payload = data.get('payload')

                # BytePlus APIにリクエスト送信
                req = urllib.request.Request(
                    endpoint,
                    data=json.dumps(payload).encode('utf-8'),
                    headers={
                        'Authorization': f'Bearer {api_key}',
                        'Content-Type': 'application/json'
                    },
                    method='POST'
                )

                # SSL証明書検証を調整（証明書エラー回避）
                context = ssl.create_default_context()
                context.check_hostname = False
                context.verify_mode = ssl.CERT_NONE

                with urllib.request.urlopen(req, context=context, timeout=60) as response:
                    result = response.read()

                    # レスポンスを返す
                    self.send_response(200)
                    self.send_header('Content-Type', 'application/json')
                    self.send_header('Access-Control-Allow-Origin', '*')
                    self.end_headers()
                    self.wfile.write(result)

            except urllib.error.HTTPError as e:
                error_body = e.read().decode('utf-8')
                print(f"API Error: {e.code} - {error_body}")

                self.send_response(e.code)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(error_body.encode('utf-8'))

            except Exception as e:
                print(f"Server Error: {str(e)}")

                self.send_response(500)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                error_response = json.dumps({'error': str(e)})
                self.wfile.write(error_response.encode('utf-8'))
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        """ログ出力"""
        print(f"{self.address_string()} - {format % args}")

if __name__ == '__main__':
    PORT = 8001
    server = HTTPServer(('localhost', PORT), ProxyHandler)
    print(f"BytePlus API Proxy Server running on http://localhost:{PORT}")
    print(f"Proxy endpoint: http://localhost:{PORT}/api/proxy")
    print("Press Ctrl+C to stop")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nServer stopped")
        server.shutdown()
