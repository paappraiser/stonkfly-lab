from __future__ import annotations

from dataclasses import dataclass
from random import Random


@dataclass
class Proposal:
    side: str
    score: float
    confidence: float


class HysteresisDecoder:
    def __init__(self, threshold: float, hysteresis: float, seed: int = 0, explore: float = 0.2):
        self.threshold = float(threshold)
        self.hysteresis = float(hysteresis)
        self.last_side = "HOLD"
        self.rng = Random(seed)
        self.explore = float(explore)

    def decode(self, score: float) -> Proposal:
        thr = self.threshold
        if self.last_side == "BUY":
            buy_thr, sell_thr = thr - self.hysteresis, -(thr + self.hysteresis)
        elif self.last_side == "SELL":
            buy_thr, sell_thr = thr + self.hysteresis, -(thr - self.hysteresis)
        else:
            buy_thr, sell_thr = thr, -thr
        if score >= buy_thr:
            side = "BUY"
        elif score <= sell_thr:
            side = "SELL"
        elif self.rng.random() < self.explore:
            side = "BUY" if score >= 0 else "SELL"
        else:
            side = "HOLD"
        self.last_side = side
        return Proposal(side=side, score=float(score), confidence=abs(float(score)))
