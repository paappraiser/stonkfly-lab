from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .broker import PaperBroker
from .config import Settings
from .market import Quote


@dataclass
class Decision:
    side: str
    reason: str
    size: float


class Guard:
    def __init__(self, settings: Settings, run_dir: Path):
        self.settings = settings
        self.stop_file = run_dir / "STOP"

    def check(self, broker: PaperBroker, quote: Quote, proposed: str) -> Decision:
        s = self.settings
        if self.stop_file.exists():
            return Decision("HOLD", "STOP file", 0.0)
        if broker.halted:
            return Decision("HOLD", f"halted: {broker.halt_reason}", 0.0)
        equity = broker.equity(quote.mid)
        if equity <= broker.start_cash - s.loss_stop:
            broker.halt("lifetime drawdown")
            return Decision("FLATTEN" if s.flatten_on_halt else "HOLD", "loss stop", 0.0)
        if broker.day_realized <= -s.daily_loss_cap:
            broker.halt("daily loss cap")
            return Decision("FLATTEN" if s.flatten_on_halt else "HOLD", "daily loss", 0.0)
        if abs(time_age(quote.ts)) > s.max_quote_age:
            return Decision("HOLD", "stale quote", 0.0)
        if proposed == "HOLD":
            if broker.qty > 0 and broker.steps_held >= s.max_hold_steps:
                return Decision("SELL", "time stop", s.order_notional)
            return Decision("HOLD", "decoder hold", 0.0)
        if proposed == "BUY":
            if broker.cash < 2.0:
                return Decision("HOLD", "no cash", 0.0)
            return Decision("BUY", "neural buy", s.order_notional)
        if proposed == "SELL":
            if broker.qty <= 0:
                return Decision("HOLD", "no inventory", 0.0)
            return Decision("SELL", "neural sell", s.order_notional)
        return Decision("HOLD", "unknown", 0.0)


def time_age(ts: float) -> float:
    import time
    return time.time() - ts
