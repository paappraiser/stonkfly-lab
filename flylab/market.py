from __future__ import annotations

import json
import random
import time
import urllib.request
from dataclasses import dataclass, field

COINBASE = "https://api.exchange.coinbase.com"


@dataclass
class Quote:
    product: str
    bid: float
    ask: float
    mid: float
    ts: float
    history: list[float] = field(default_factory=list)

    @property
    def ret(self) -> float:
        if len(self.history) < 2 or self.history[-2] == 0:
            return 0.0
        return self.history[-1] / self.history[-2] - 1.0

    @property
    def vol(self) -> float:
        if len(self.history) < 6:
            return abs(self.ret)
        diffs = []
        for a, b in zip(self.history[-6:-1], self.history[-5:]):
            if a:
                diffs.append(abs(b / a - 1.0))
        return sum(diffs) / max(len(diffs), 1)


def _get(url: str) -> object:
    req = urllib.request.Request(url, headers={"User-Agent": "stonkfly-lab/0.1"})
    with urllib.request.urlopen(req, timeout=10) as resp:
        return json.loads(resp.read().decode())


class LiveTape:
    def __init__(self, product: str = "BTC-USD"):
        self.product = product
        self.history: list[float] = []

    def seed(self) -> None:
        url = f"{COINBASE}/products/{self.product}/candles?granularity=60"
        raw = _get(url)
        closes = [float(row[4]) for row in sorted(raw, key=lambda r: r[0])]
        self.history = closes[-120:]

    def quote(self) -> Quote:
        url = f"{COINBASE}/products/{self.product}/ticker"
        data = _get(url)
        bid = float(data["bid"])
        ask = float(data["ask"])
        mid = (bid + ask) / 2.0
        if not self.history or abs(mid - self.history[-1]) > 0:
            self.history.append(mid)
            self.history = self.history[-240:]
        return Quote(self.product, bid, ask, mid, time.time(), list(self.history))


class ReplayTape:
    def __init__(self, product: str = "BTC-USD", seed: int = 7):
        self.product = product
        self.seed = seed
        self.closes: list[float] = []
        self.i = 1

    def seed(self) -> None:
        try:
            url = f"{COINBASE}/products/{self.product}/candles?granularity=60"
            raw = _get(url)
            closes = [float(row[4]) for row in sorted(raw, key=lambda r: r[0])]
            self.closes = closes[-300:] or [100.0]
        except Exception:
            rng = random.Random(self.seed)
            price = 100.0
            self.closes = [price]
            for _ in range(300):
                price = max(1.0, price * (1.0 + rng.gauss(0.0001, 0.004)))
                self.closes.append(price)
        self.i = 2

    def quote(self) -> Quote:
        if self.i >= len(self.closes):
            self.i = 2
        mid = self.closes[self.i]
        hist = self.closes[: self.i + 1]
        self.i += 1
        spread = mid * 0.0004
        return Quote(self.product + "-REPLAY", mid - spread / 2, mid + spread / 2, mid, time.time(), hist)


class FixtureTape:
    def __init__(self, start: float = 100.0, seed: int = 7):
        self.product = "FIXTURE-USD"
        self.price = start
        self.rng = random.Random(seed)
        self.history = [start]

    def seed(self) -> None:
        for _ in range(80):
            self._step()

    def _step(self) -> None:
        shock = self.rng.gauss(0.0002, 0.006)
        self.price = max(1.0, self.price * (1.0 + shock))
        self.history.append(self.price)
        self.history = self.history[-240:]

    def quote(self) -> Quote:
        self._step()
        mid = self.price
        spread = mid * 0.0004
        return Quote(self.product, mid - spread / 2, mid + spread / 2, mid, time.time(), list(self.history))
