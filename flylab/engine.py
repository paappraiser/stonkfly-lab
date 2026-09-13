from __future__ import annotations

import json
import threading
import time

from .broker import PaperBroker
from .colony import Colony
from .config import Settings
from .market import FixtureTape, LiveTape, Quote
from .reinforcement import grade
from .risk import Guard
from .vision import render_ppm
from .worlds import RuleWorld, Stage0World


class Engine:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.run_dir = settings.run_dir()
        self.colony = Colony(settings)
        self.broker = PaperBroker.load(self.run_dir / "ledger.json", settings.starting_cash, settings.fee_bps)
        self.guard = Guard(settings, self.run_dir)
        if settings.world == "stage0":
            self.world = Stage0World(settings.seed)
        elif settings.world == "rule":
            self.world = RuleWorld(settings.seed)
        else:
            self.world = None
        self.tape: LiveTape | FixtureTape = LiveTape(settings.product) if settings.world == "market" else FixtureTape(seed=settings.seed)
        self.pending = None
        self.step_i = 0
        self.events = []
        self.alive = True
        self.lock = threading.Lock()
        self.metrics = {"agreements": 0, "disagreements": 0, "correct_stage0": 0, "stage0_decisions": 0, "fills": 0}

    def prepare(self) -> None:
        self.tape.seed()
        try:
            (self.run_dir / "settings.json").write_text(json.dumps(self.settings.signature(), indent=2))
        except OSError:
            pass

    def once(self) -> dict:
        with self.lock:
            return self._once()

    def _once(self) -> dict:
        s = self.settings
        planted = target = None
        if self.world:
            obs = self.world.observe()
            planted, target = obs.pattern, obs.target
            quote = Quote("STAGE0", 100, 100, 100, time.time(), [100, 100 + obs.ret * 100])
            ret, vol, pos = obs.ret, obs.vol, self.broker.qty
        else:
            quote = self.tape.quote()
            self.broker.mark(quote.mid)
            ret, vol, pos = quote.ret, quote.vol, self.broker.qty
        if self.pending and not s.frozen:
            valence = self._settle(quote)
            action = str(self.pending.get("action", "HOLD"))
            if self.world:
                if action == "SELL":
                    valence = -valence
                elif action not in {"BUY", "SELL"}:
                    valence = 0.0
            if valence != 0:
                self.colony.reinforce_all(self.pending["elig"], valence)
            self.pending = None
        odor = self.colony.perceive(ret=ret, vol=vol, position_qty=pos, planted=planted)
        step = self.colony.decide(odor)
        self.metrics["agreements" if step.agreement else "disagreements"] += 1
        proposed = step.joint.side
        fill = None
        fee = 0.0
        if self.world:
            self.metrics["stage0_decisions"] += 1
            if proposed == target:
                self.metrics["correct_stage0"] += 1
            reason = "stage0"
            executed = proposed
            self.broker.cash += self.world.outcome(proposed, target)
            equity_after = self.broker.equity(quote.mid)
        else:
            decision = self.guard.check(self.broker, quote, proposed)
            executed, reason = decision.side, decision.reason
            if executed == "FLATTEN":
                fill = self.broker.flatten(quote.bid, quote.ask, reason)
                executed = fill.side if fill else "HOLD"
            elif executed in {"BUY", "SELL"}:
                fill = self.broker.market_order(executed, decision.size, quote.bid, quote.ask, reason)
            if fill:
                fee = fill.fee
                self.metrics["fills"] += 1
            equity_after = self.broker.equity(quote.mid)
        self.pending = {"elig": self.colony.snapshots(), "action": executed, "filled": fill is not None, "fee": fee, "equity": equity_after, "target": target}
        try:
            render_ppm(self.run_dir / "latest.ppm", quote, odor.name, executed, equity_after)
        except OSError:
            pass
        event = {
            "step": self.step_i,
            "ts": time.time(),
            "product": quote.product,
            "mid": quote.mid,
            "bid": quote.bid,
            "ask": quote.ask,
            "ret": ret,
            "vol": vol,
            "odor": odor.name,
            "labels": odor.labels,
            "proposals": [{"side": p.side, "score": p.score} for p in step.proposals],
            "joint": {"side": step.joint.side, "score": step.joint.score},
            "executed": executed,
            "reason": reason,
            "agreement": step.agreement,
            "banner": step.banner,
            "equity": equity_after,
            "cash": self.broker.cash,
            "qty": self.broker.qty,
            "fee": fee,
            "halted": self.broker.halted,
            "halt_reason": self.broker.halt_reason,
            "flies": [{"name": st.name, "score": st.score, "sparsity": st.sparsity, "weight_drift": st.weight_drift} for st in step.flies],
            "metrics": dict(self.metrics),
            "stage0_target": target,
            "stage0_acc": (self.metrics["correct_stage0"] / self.metrics["stage0_decisions"] if self.metrics["stage0_decisions"] else None),
            "history": quote.history[-80:],
        }
        self.events.append(event)
        self.events = self.events[-400:]
        self._write_state(event)
        try:
            self.broker.save()
        except OSError:
            pass
        self.step_i += 1
        return event

    def _settle(self, quote: Quote) -> float:
        pending = self.pending or {}
        if self.world:
            return self.world.outcome(str(pending.get("action", "HOLD")), pending.get("target"))
        s = self.settings
        equity_now = self.broker.equity(quote.mid)
        return grade(
            equity_now=equity_now,
            equity_then=float(pending.get("equity", equity_now)),
            action=str(pending.get("action", "HOLD")),
            filled=bool(pending.get("filled")),
            fee_paid=float(pending.get("fee", 0.0)),
            deadband=s.deadband,
            exclude_fees=s.exclude_fees_from_reward,
            proportional=s.proportional_dopamine,
            order_notional=s.order_notional,
        ).valence

    def _write_state(self, event: dict) -> None:
        payload = {
            "event": event,
            "equity_curve": self.broker.equity_curve[-300:],
            "fills": [asdict_fill(f) for f in self.broker.fills[-40:]],
            "settings": {"world": self.settings.world, "colony": self.settings.colony, "n_flies": self.settings.n_flies, "product": self.settings.product, "fee_bps": self.settings.fee_bps, "frozen": self.settings.frozen},
        }
        try:
            (self.run_dir / "latest.json").write_text(json.dumps(payload))
            with (self.run_dir / "events.jsonl").open("a") as fh:
                fh.write(json.dumps(event) + "\n")
        except OSError:
            pass

    def run(self) -> None:
        self.prepare()
        n = self.settings.steps
        i = 0
        while self.alive:
            if (self.run_dir / "STOP").exists():
                break
            self.once()
            i += 1
            if n and i >= n:
                break
            if not self.settings.fast:
                time.sleep(self.settings.interval_seconds)

    def stop(self) -> None:
        self.alive = False


def asdict_fill(fill) -> dict:
    return {"ts": fill.ts, "side": fill.side, "qty": fill.qty, "price": fill.price, "fee": fill.fee, "notional": fill.notional, "note": fill.note}
