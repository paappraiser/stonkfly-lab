from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .config import Settings


@dataclass
class FlyState:
    name: str
    pn: np.ndarray
    kc: np.ndarray
    mbon_buy: np.ndarray
    mbon_sell: np.ndarray
    eligibility: np.ndarray
    score: float
    sparsity: float
    weight_drift: float


class MushroomBody:
    def __init__(self, settings: Settings, name: str, seed: int):
        self.settings = settings
        self.name = name
        rng = np.random.default_rng(seed)
        n_kc = settings.n_kc
        n_pn = settings.n_pn
        self.pn_to_kc = np.zeros((n_kc, n_pn), dtype=np.float64)
        for i in range(n_kc):
            idx = rng.choice(n_pn, size=min(settings.kc_inputs, n_pn), replace=False)
            self.pn_to_kc[i, idx] = rng.uniform(0.6, 1.2, size=idx.size)
        self.kc_bias = rng.normal(0.0, 0.05, size=n_kc)
        n_buy = settings.n_mbon_buy
        n_sell = settings.n_mbon_sell
        self.w_buy0 = rng.uniform(0.8, 1.2, size=(n_kc, n_buy)) / n_kc
        self.w_sell0 = rng.uniform(0.8, 1.2, size=(n_kc, n_sell)) / n_kc
        self.w_buy = self.w_buy0.copy()
        self.w_sell = self.w_sell0.copy()
        self.eligibility = np.zeros(n_kc, dtype=np.float64)
        self.last = FlyState(name=name, pn=np.zeros(n_pn), kc=np.zeros(n_kc), mbon_buy=np.zeros(n_buy), mbon_sell=np.zeros(n_sell), eligibility=self.eligibility.copy(), score=0.0, sparsity=0.0, weight_drift=0.0)

    def step(self, pn: np.ndarray) -> FlyState:
        s = self.settings
        drive = self.pn_to_kc @ pn + self.kc_bias
        k = max(1, int(round(s.sparsity_target * s.n_kc)))
        thresh = np.partition(drive, -k)[-k]
        kc = np.clip(drive - thresh, 0.0, None)
        if kc.max() > 0:
            kc = kc / (kc.max() + 1e-9)
        buy = kc @ self.w_buy * s.n_kc
        sell = kc @ self.w_sell * s.n_kc
        denom = abs(float(buy.mean())) + abs(float(sell.mean())) + 1e-9
        score = float(buy.mean() - sell.mean()) / denom
        self.eligibility *= 1.0 - s.eligibility_decay
        self.eligibility += kc
        drift = float(np.mean(np.abs(self.w_buy / (self.w_buy0 + 1e-12) - 1.0)) + np.mean(np.abs(self.w_sell / (self.w_sell0 + 1e-12) - 1.0)))
        self.last = FlyState(name=self.name, pn=np.asarray(pn, dtype=np.float64), kc=kc, mbon_buy=buy, mbon_sell=sell, eligibility=self.eligibility.copy(), score=score, sparsity=float(np.mean(kc > 0)), weight_drift=drift)
        return self.last

    def snapshot_eligibility(self) -> np.ndarray:
        return self.last.kc.copy()

    def reinforce(self, eligibility: np.ndarray, valence: float) -> None:
        if self.settings.frozen or valence == 0.0:
            return
        s = self.settings
        e = np.clip(eligibility, 0.0, None)
        if e.max() > 0:
            e = e / (e.max() + 1e-9)
        step = s.eta * float(np.clip(valence, -1.0, 1.0))
        self.w_buy += np.outer(e, np.ones(s.n_mbon_buy)) * (step / max(s.n_kc * s.sparsity_target, 1.0))
        self.w_sell -= np.outer(e, np.ones(s.n_mbon_sell)) * (step / max(s.n_kc * s.sparsity_target, 1.0))
        self._decay_and_clip()

    def dashboard(self) -> dict:
        buy_shift = float(np.mean(self.w_buy / (self.w_buy0 + 1e-12) - 1.0))
        sell_shift = float(np.mean(self.w_sell / (self.w_sell0 + 1e-12) - 1.0))
        kc = self.last.kc
        bins = 48
        preview = []
        if kc.size:
            step = max(1, kc.size // bins)
            preview = [round(float(kc[i : i + step].mean()), 4) for i in range(0, kc.size, step)][:bins]
        return {"buy_shift": buy_shift, "sell_shift": sell_shift, "buy": float(self.last.mbon_buy.mean()) if self.last.mbon_buy.size else 0.0, "sell": float(self.last.mbon_sell.mean()) if self.last.mbon_sell.size else 0.0, "kc_preview": preview}

    def reset_memory(self) -> None:
        self.w_buy = self.w_buy0.copy()
        self.w_sell = self.w_sell0.copy()
        self.eligibility[:] = 0

    def _decay_and_clip(self) -> None:
        s = self.settings
        self.w_buy -= s.memory_decay * (self.w_buy - self.w_buy0)
        self.w_sell -= s.memory_decay * (self.w_sell - self.w_sell0)
        np.clip(self.w_buy, s.weight_min * self.w_buy0, s.weight_max * self.w_buy0, out=self.w_buy)
        np.clip(self.w_sell, s.weight_min * self.w_sell0, s.weight_max * self.w_sell0, out=self.w_sell)
