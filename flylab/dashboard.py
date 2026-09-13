from __future__ import annotations

import struct
import threading
import zlib
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

WEB = Path(__file__).resolve().parent / "web"


class QuietServer(ThreadingHTTPServer):
    def handle_error(self, request, client_address) -> None:
        return


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, run_dir: Path, **kwargs):
        self.run_dir = run_dir
        super().__init__(*args, directory=str(WEB), **kwargs)

    def log_message(self, fmt: str, *args) -> None:
        pass

    def do_GET(self) -> None:
        try:
            if self.path.startswith("/api/state"):
                path = self.run_dir / "latest.json"
                body = path.read_bytes() if path.exists() else b"{}"
                self._send(body, "application/json")
                return
            if self.path.startswith("/api/frame"):
                path = self.run_dir / "latest.ppm"
                if not path.exists():
                    self.send_error(404)
                    return
                png = _ppm_to_png(path.read_bytes())
                if not png:
                    self.send_error(404)
                    return
                self._send(png, "image/png")
                return
            super().do_GET()
        except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError):
            return

    def _send(self, body: bytes, ctype: str) -> None:
        self.send_response(200)
        self.send_header("Content-Type", ctype)
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        try:
            self.wfile.write(body)
        except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError):
            return


def serve(host: str, port: int, run_dir: Path) -> ThreadingHTTPServer:
    handler = partial(Handler, run_dir=run_dir)
    httpd = QuietServer((host, port), handler)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    return httpd


def _ppm_to_png(ppm: bytes) -> bytes:
    if not ppm.startswith(b"P6"):
        return b""
    header, _, rest = ppm.partition(b"\n")
    parts = header.split()
    if len(parts) < 3:
        return b""
    w, h = int(parts[1]), int(parts[2])
    if rest.startswith(b"255"):
        rest = rest.split(b"\n", 1)[1]
    raw = bytearray()
    row = w * 3
    for y in range(h):
        raw.append(0)
        raw.extend(rest[y * row : (y + 1) * row])

    def chunk(tag: bytes, data: bytes) -> bytes:
        crc = zlib.crc32(tag + data) & 0xFFFFFFFF
        return struct.pack(">I", len(data)) + tag + data + struct.pack(">I", crc)

    ihdr = struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0)
    return b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr) + chunk(b"IDAT", zlib.compress(bytes(raw), 9)) + chunk(b"IEND", b"")
