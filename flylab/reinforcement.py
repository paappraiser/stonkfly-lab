from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Outcome:
    kind: str
    valence: float
    raw_delta: float
    note: str


def grade(
    *,
    equity_now: float,
    equity_then: float,
    action: str,
    filled: bool,
    fee_paid: float,
    deadband: float,
    exclude_fees: bool,
    proportional: bool,
    order_notional: float,
) -> Outcome:
    delta = equity_now - equity_then
    if exclude_fees:
        delta += fee_paid
    if action == "HOLD" and not filled and abs(delta) < deadband:
        return Outcome("none", 0.0, delta, "hold-deadband")
    if abs(delta) < deadband:
        return Outcome("none", 0.0, delta, "deadband")
    scale = max(order_notional, 1e-9)
    valence = delta / scale
    if not proportional:
        valence = 1.0 if delta > 0 else -1.0
    valence = max(-1.0, min(1.0, valence))
    kind = "reward" if valence > 0 else "aversive"
    return Outcome(kind, valence, delta, f"{action}:{'fill' if filled else 'mark'}")
