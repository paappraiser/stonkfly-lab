from __future__ import annotations

from dataclasses import dataclass
import time

import numpy as np

GROUPS = {
    "move": ("down_strong", "down", "flat", "up", "up_strong"),
    "lag": ("down_strong", "down", "flat", "up", "up_strong"),
    "vol": ("calm", "normal", "wild"),
    "pos": ("flat", "long", "short"),
    "session": ("asia", "london", "ny", "off"),
    "partner": ("hold", "buy", "sell"),
}
GROUP_SIZES = {name: len(labels) for name, labels in GROUPS.items()}


def pn_layout(n_pn: int) -> dict[str, slice]:
    names = list(GROUPS)
    widths, remaining = [], n_pn
    for i, name in enumerate(names):
        if i == len(names) - 1:
            widths.append(remaining)
        else:
            w = max(GROUP_SIZES[name], remaining // (len(names) - i))
            w = min(w, remaining - (len(names) - i - 1))
            widths.append(w)
            remaining -= w
    layout, cursor = {}, 0
    for name, width in zip(names, widths):
        layout[name] = slice(cursor, cursor + width)
        cursor += width
    return layout


@dataclass
class Odor:
    name: str
    vector: np.ndarray
    labels: dict[str, str]


def _one_hot_fill(n: int, index: int) -> np.ndarray:
    vec = np.zeros(n, dtype=np.float64)
    if n <= 0:
        return vec
    index = int(np.clip(index, 0, n - 1))
    for offset, amp in ((-1, 0.35), (0, 1.0), (1, 0.35)):
        j = index + offset
        if 0 <= j < n:
            vec[j] = max(vec[j], amp)
    return vec


def move_bin(ret: float) -> int:
    if ret <= -0.012:
        return 0
    if ret <= -0.003:
        return 1
    if ret < 0.003:
        return 2
    if ret < 0.012:
        return 3
    return 4


def vol_bin(vol: float) -> int:
    if vol < 0.004:
        return 0
    if vol < 0.012:
        return 1
    return 2


def pos_bin(position_qty: float) -> int:
    if position_qty > 1e-12:
        return 1
    if position_qty < -1e-12:
        return 2
    return 0


def partner_bin(side: str) -> int:
    return {"HOLD": 0, "BUY": 1, "SELL": 2}.get(side, 0)


def session_bin(ts: float | None = None) -> int:
    hour = time.gmtime(ts or time.time()).tm_hour
    if 0 <= hour < 7:
        return 0
    if 7 <= hour < 13:
        return 1
    if 13 <= hour < 21:
        return 2
    return 3


class OdorEncoder:
    def __init__(self, n_pn: int):
        self.n_pn = int(n_pn)
        self.layout = pn_layout(self.n_pn)
        self.ret_hist: list[float] = []

    def encode(self, *, ret: float, vol: float, position_qty: float, partner_side: str = "HOLD", include_partner: bool = True) -> Odor:
        self.ret_hist.append(float(ret))
        self.ret_hist = self.ret_hist[-8:]
        lag = self.ret_hist[0] if len(self.ret_hist) >= 5 else 0.0
        labels = {
            "move": GROUPS["move"][move_bin(ret)],
            "lag": GROUPS["lag"][move_bin(lag)],
            "vol": GROUPS["vol"][vol_bin(vol)],
            "pos": GROUPS["pos"][pos_bin(position_qty)],
            "session": GROUPS["session"][session_bin()],
            "partner": GROUPS["partner"][partner_bin(partner_side)],
        }
        vector = np.zeros(self.n_pn, dtype=np.float64)
        for group, label in labels.items():
            if group == "partner" and not include_partner:
                continue
            sl = self.layout[group]
            width = sl.stop - sl.start
            idx = GROUPS[group].index(label)
            center = int(round((idx / max(len(GROUPS[group]) - 1, 1)) * max(width - 1, 0)))
            vector[sl] = _one_hot_fill(width, center)
        name = "{move}|{lag}|{vol}|{pos}|{session}|{partner}".format(**labels)
        return Odor(name=name, vector=vector, labels=labels)

    def planted(self, pattern: str) -> Odor:
        vector = np.zeros(self.n_pn, dtype=np.float64)
        sl = self.layout["move"]
        width = sl.stop - sl.start
        if pattern == "A":
            vector[sl] = _one_hot_fill(width, width - 1)
            labels = {"move": "up_strong", "lag": "flat", "vol": "calm", "pos": "flat", "session": "off", "partner": "hold"}
        elif pattern == "B":
            vector[sl] = _one_hot_fill(width, 0)
            labels = {"move": "down_strong", "lag": "flat", "vol": "calm", "pos": "flat", "session": "off", "partner": "hold"}
        else:
            labels = {"move": "flat", "lag": "flat", "vol": "calm", "pos": "flat", "session": "off", "partner": "hold"}
            vector[self.layout["vol"]] = 0.4
        return Odor(name=f"planted-{pattern}", vector=vector, labels=labels)
