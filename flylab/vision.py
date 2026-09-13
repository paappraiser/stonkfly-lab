from __future__ import annotations

from pathlib import Path

from .market import Quote


def render_ppm(path: Path, quote: Quote, odor_name: str, side: str, equity: float) -> None:
    w, h = 240, 120
    bg = (18, 22, 30)
    pixels = [bg] * (w * h)
    hist = quote.history[-80:] or [quote.mid]
    lo, hi = min(hist), max(hist)
    span = max(hi - lo, quote.mid * 0.002, 1e-9)

    def put(x: int, y: int, rgb: tuple[int, int, int]) -> None:
        if 0 <= x < w and 0 <= y < h:
            pixels[y * w + x] = rgb

    for x in range(0, w, 32):
        for y in range(h):
            put(x, y, (28, 34, 46))
    for i, px in enumerate(hist):
        x = int(i / max(len(hist) - 1, 1) * (w - 21)) + 10
        y = int((1.0 - (px - lo) / span) * (h - 31)) + 18
        color = (46, 204, 113) if i == 0 or px >= hist[i - 1] else (231, 76, 60)
        for dx in range(-1, 2):
            for dy in range(-1, 2):
                put(x + dx, y + dy, color)
    ret = quote.ret
    radius = int(6 + min(abs(ret) * 1800, 28))
    cx, cy = w - 36, 36
    fill = (46, 204, 113) if ret >= 0 else (231, 76, 60)
    for y in range(cy - radius, cy + radius + 1):
        for x in range(cx - radius, cx + radius + 1):
            if (x - cx) ** 2 + (y - cy) ** 2 <= radius * radius:
                put(x, y, fill)
    header = f"P6 {w} {h} 255\n".encode()
    raw = bytes(c for rgb in pixels for c in rgb)
    path.write_bytes(header + raw)
