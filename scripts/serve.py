"""
支援 Range Request 的 HTTP Server
用途：讓瀏覽器可以對影片做跳轉（seek）
用法：python scripts/serve.py
"""
import http.server
import os
import sys


class RangeHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):

    def do_GET(self):
        range_header = self.headers.get('Range')
        if range_header and not os.path.isdir(self.translate_path(self.path)):
            self._serve_range(range_header)
        else:
            f = self.send_head()
            if f:
                try:
                    self.copyfile(f, self.wfile)
                finally:
                    f.close()

    def send_head(self):
        path = self.translate_path(self.path)
        if os.path.isdir(path):
            return super().send_head()
        try:
            f = open(path, 'rb')
        except OSError:
            self.send_error(404, "File not found")
            return None
        try:
            fs = os.fstat(f.fileno())
            self.send_response(200)
            self.send_header('Content-Type', self.guess_type(path))
            self.send_header('Content-Length', str(fs[6]))
            self.send_header('Accept-Ranges', 'bytes')
            self.send_header('Last-Modified', self.date_time_string(fs.st_mtime))
            self.end_headers()
            return f
        except Exception:
            f.close()
            raise

    def _serve_range(self, range_header):
        path = self.translate_path(self.path)
        try:
            f = open(path, 'rb')
        except OSError:
            self.send_error(404, "File not found")
            return
        try:
            file_size = os.fstat(f.fileno())[6]
            byte_range = range_header.strip().replace('bytes=', '')
            parts = byte_range.split('-')
            start = int(parts[0]) if parts[0] else 0
            end = int(parts[1]) if len(parts) > 1 and parts[1] else file_size - 1
            start = max(0, start)
            end = min(end, file_size - 1)
            length = end - start + 1

            f.seek(start)
            self.send_response(206)
            self.send_header('Content-Type', self.guess_type(path))
            self.send_header('Content-Range', f'bytes {start}-{end}/{file_size}')
            self.send_header('Content-Length', str(length))
            self.send_header('Accept-Ranges', 'bytes')
            self.end_headers()

            remaining = length
            while remaining > 0:
                chunk = f.read(min(65536, remaining))
                if not chunk:
                    break
                self.wfile.write(chunk)
                remaining -= len(chunk)
        finally:
            f.close()

    def log_message(self, format, *args):
        status = args[1] if len(args) > 1 else ''
        if status != '206':
            super().log_message(format, *args)


if __name__ == '__main__':
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8000
    server = http.server.HTTPServer(('', port), RangeHTTPRequestHandler)
    print(f'Serving on http://localhost:{port}')
    print('Range Request 支援已啟用（影片可正常跳轉）')
    server.serve_forever()
