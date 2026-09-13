from __future__ import annotations

import random
from dataclasses import dataclass


@dataclass
class PlantedObs:
    pattern: str
    target: str
    ret: float
    vol: float


class Stage0World:
    """Two odors with a planted correct action. Used to prove the wire learns."""

    def __init__(self, seed: int = 7):
        self.rng = random.Random(seed)
        self.last: PlantedObs | None = None

    def observe(self) -> PlantedObs:
        pattern = self.rng.choice(["A", "B"])
        target = "BUY" if pattern == "A" else "SELL"
        ret = 0.02 if pattern == "A" else -0.02
        self.last = PlantedObs(pattern, target, ret, 0.002)
        return self.last

    def outcome(self, action: str) -> float:
        if not self.last:
            return 0.0
        if action == self.last.target:
            return 0.8
        if action == "HOLD":
            return 0.0
        return -0.8
