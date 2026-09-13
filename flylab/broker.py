from __future__ import annotations

import json
import time
from dataclasses import asdict, dataclass
from pathlib import Path


@dataclass
class Fill:
    ts: float
    side: str
    qty: float
    price: float
    fee: float
    notional: float
    note: str


class PaperBroker:
    def __init__(self, path: Path, cash: float, fee_bps: float):
        self.path = path
        self.cash = float(cash)
        self.start_cash = float(cash)
        self.qty = 0.0
        self.fee_bps = float(fee_bps)
        self.fills: list[Fill] = []
        self.halted = False
        self.halt_reason = ""
        self.equity_curve: list[tuple[float, float]] = []
        self.day_realized = 0.0
        self.day_stamp = time.strftime("%Y-%m-%d")
        self.entry_step: int | None = None
        self.steps_held = 0
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def equity(self, mid: float) -> float:
        return self.cash + self.qty * mid

    def mark(self, mid: float) -> None:
        today = time.strftime("%Y-%m-%d")
        if today != self.day_stamp:
            self.day_stamp = today
            self.day_realized = 0.0
        self.equity_curve.append((time.time(), self.equity(mid)))
        self.equity_curve = self.equity_curve[-2000:]
        if self.qty != 0:
            self.steps_held += 1
        else:
            self.steps_held = 0
            self.entry_step = None

    def market_order(self, side: str, notional: float, bid: float, ask: float, note: str = "") -> Fill | None:
        if self.halted:
            return None
        fee_rate = self.fee_bps / 10_000.0
        if side == "BUY":
            px = ask
            gross = min(notional, self.cash / (1.0 + fee_rate))
            if gross < 1.0 or px <= 0:
                return None
            qty = gross / px
            fee = gross * fee_rate
            self.cash -= gross + fee
            self.qty += qty
            fill = Fill(time.time(), side, qty, px, fee, gross, note)
        elif side == "SELL":
            px = bid
            if self.qty <= 0 or px <= 0:
                return None
            cap_qty = min(self.qty, notional / px)
            gross = cap_qty * px
            fee = gross * fee_rate
            self.cash += gross - fee
            self.qty -= cap_qty
            fill = Fill(time.time(), side, cap_qty, px, fee, gross, note)
        else:
            return None
        self.fills.append(fill)
        self.day_realized -= fill.fee
        if self.qty == 0:
            self.steps_held = 0
            self.entry_step = None
        elif self.entry_step is None:
            self.entry_step = len(self.fills)
        return fill

    def flatten(self, bid: float, ask: float, reason: str) -> Fill | None:
        if self.qty > 0:
            return self.market_order("SELL", self.qty * bid, bid, ask, reason)
        if self.qty < 0:
            return self.market_order("BUY", abs(self.qty) * ask, bid, ask, reason)
        return None

    def halt(self, reason: str) -> None:
        self.halted = True
        self.halt_reason = reason

    def save(self) -> None:
        payload = {
            "cash": self.cash,
            "qty": self.qty,
            "start_cash": self.start_cash,
            "halted": self.halted,
            "halt_reason": self.halt_reason,
            "fills": [asdict(f) for f in self.fills[-200:]],
            "equity_curve": self.equity_curve[-500:],
            "day_realized": self.day_realized,
            "day_stamp": self.day_stamp,
            "steps_held": self.steps_held,
        }
        try:
            self.path.write_text(json.dumps(payload, indent=2))
        except OSError:
            pass

    @classmethod
    def load(cls, path: Path, cash: float, fee_bps: float) -> "PaperBroker":
        broker = cls(path, cash, fee_bps)
        if not path.exists():
            return broker
        data = json.loads(path.read_text())
        broker.cash = float(data["cash"])
        broker.qty = float(data["qty"])
        broker.start_cash = float(data.get("start_cash", cash))
        broker.halted = bool(data.get("halted"))
        broker.halt_reason = data.get("halt_reason", "")
        broker.day_realized = float(data.get("day_realized", 0))
        broker.day_stamp = data.get("day_stamp", broker.day_stamp)
        broker.steps_held = int(data.get("steps_held", 0))
        broker.equity_curve = [tuple(x) for x in data.get("equity_curve", [])]
        broker.fills = [Fill(**f) for f in data.get("fills", [])]
        return broker
