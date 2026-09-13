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

    def outcome(self, action: str, target: str | None = None) -> float:
        want = target if target is not None else (self.last.target if self.last else None)
        if not want:
            return 0.0
        if action == want:
            return 0.8
        if action == "HOLD":
            return 0.0
        return -0.8


class RuleWorld:
    """Signed-return teacher. Same two smells as Stage 0, jittered magnitude."""

    def __init__(self, seed: int = 7, deadband: float = 0.003):
        self.rng = random.Random(seed)
        self.deadband = deadband
        self.last: PlantedObs | None = None

    def observe(self) -> PlantedObs:
        roll = self.rng.random()
        if roll < 0.5:
            ret = self.rng.uniform(0.013, 0.028)
            target, pattern = "BUY", "A"
        else:
            ret = -self.rng.uniform(0.013, 0.028)
            target, pattern = "SELL", "B"
        vol = self.rng.uniform(0.006, 0.014)
        self.last = PlantedObs(pattern, target, ret, vol)
        return self.last

    def outcome(self, action: str, target: str | None = None) -> float:
        want = target if target is not None else (self.last.target if self.last else None)
        if not want:
            return 0.0
        if want == "HOLD":
            return 0.0
        if action == want:
            return 0.8
        if action == "HOLD":
            return 0.0
        return -0.8
