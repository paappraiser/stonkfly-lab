from __future__ import annotations

import argparse
import json
from pathlib import Path

from .config import Settings
from .dashboard import serve
from .engine import Engine


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="flylab", description="Stonkfly Lab")
    sub = p.add_subparsers(dest="cmd", required=True)

    def add_shared(sp: argparse.ArgumentParser) -> None:
        sp.add_argument("--world", choices=["stage0", "rule", "market", "fixture", "replay"], default="stage0")
        sp.add_argument("--colony", choices=["solo", "agree", "soft", "governor"], default="agree")
        sp.add_argument("--clone", action="store_true")
        sp.add_argument("--flies", type=int, default=2)
        sp.add_argument("--product", default="BTC-USD")
        sp.add_argument("--steps", type=int, default=0)
        sp.add_argument("--fast", action="store_true")
        sp.add_argument("--frozen", action="store_true")
        sp.add_argument("--shuffle-reward", action="store_true")
        sp.add_argument("--out", default="runs/paper")
        sp.add_argument("--interval", type=float, default=15.0)
        sp.add_argument("--fee-bps", type=float, default=8.0)
        sp.add_argument("--port", type=int, default=7474)
        sp.add_argument("--no-dashboard", action="store_true")
        sp.add_argument("--seed", type=int, default=7)
        sp.add_argument("--eta", type=float, default=0.25)
        sp.add_argument("--decay", type=float, default=0.001)
        sp.add_argument("--load", default="")

    run = sub.add_parser("run", help="run the experiment loop")
    add_shared(run)
    demo = sub.add_parser("demo")
    demo.add_argument("--steps", type=int, default=250)
    demo.add_argument("--out", default="runs/demo")
    demo.add_argument("--port", type=int, default=7474)
    sub.add_parser("doctor")
    twins = sub.add_parser("twins")
    twins.add_argument("--world", choices=["stage0", "rule"], default="stage0")
    twins.add_argument("--steps", type=int, default=200)
    school = sub.add_parser("school")
    school.add_argument("--steps", type=int, default=200)
    back = sub.add_parser("backtest")
    add_shared(back)
    return p


def settings_from(args: argparse.Namespace) -> Settings:
    world = getattr(args, "world", "stage0")
    return Settings(
        world=world,
        colony=getattr(args, "colony", "agree"),
        n_flies=getattr(args, "flies", 2),
        product=getattr(args, "product", "BTC-USD"),
        steps=getattr(args, "steps", 0),
        fast=bool(getattr(args, "fast", False) or world in {"stage0", "rule", "replay", "fixture"}),
        frozen=bool(getattr(args, "frozen", False)),
        shuffle_reward=bool(getattr(args, "shuffle_reward", False)),
        out=getattr(args, "out", "runs/paper"),
        interval_seconds=getattr(args, "interval", 15.0),
        fee_bps=getattr(args, "fee_bps", 8.0),
        dashboard_port=getattr(args, "port", 7474),
        seed=getattr(args, "seed", 7),
        clone_weights=bool(getattr(args, "clone", False)),
        eta=float(getattr(args, "eta", 0.25)),
        memory_decay=float(getattr(args, "decay", 0.001)),
        load_memory=str(getattr(args, "load", "") or ""),
    )


def _run(settings: Settings, dashboard: bool) -> Engine:
    engine = Engine(settings)
    dash = "off"
    if dashboard:
        serve(settings.dashboard_host, settings.dashboard_port, settings.run_dir())
        dash = f"http://{settings.dashboard_host}:{settings.dashboard_port}"
    print("tiny shoes on.", settings.world, settings.colony, "eta", settings.eta)
    print("dashboard", dash)
    engine.run()
    return engine


def run_twins(world: str, steps: int):
    results = {}
    for name, frozen, shuffle in (("plastic", False, False), ("frozen", True, False), ("shuffled", False, True)):
        s = Settings(world=world, colony="solo", n_flies=1, steps=steps, fast=True, frozen=frozen, shuffle_reward=shuffle, out=f"runs/twin-{world}-{name}", seed=7)
        engine = Engine(s)
        engine.run()
        acc = engine.metrics["correct_stage0"] / max(engine.metrics["stage0_decisions"], 1)
        results[name] = acc
        print(f"  {world:7} {name:10}  acc={acc:.1%}")
    Path("runs").mkdir(parents=True, exist_ok=True)
    Path(f"runs/twins-{world}.json").write_text(json.dumps(results, indent=2))
    ok = results["plastic"] > results["frozen"] and results["plastic"] > results["shuffled"]
    print(("pass" if ok else "fail") + f"  {world}")
    return ok, results


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    if args.cmd == "doctor":
        print("ok. python -m flylab twins")
        return 0
    if args.cmd == "demo":
        engine = _run(Settings(world="stage0", colony="solo", n_flies=1, steps=args.steps, fast=True, out=args.out, dashboard_port=args.port), True)
        acc = engine.metrics["correct_stage0"] / max(engine.metrics["stage0_decisions"], 1)
        print(f"stage0 accuracy {acc:.1%}")
        return 0 if acc > 0.6 else 1
    if args.cmd == "twins":
        ok, _ = run_twins(args.world, args.steps)
        return 0 if ok else 1
    if args.cmd == "school":
        ok1, _ = run_twins("stage0", args.steps)
        ok2, _ = run_twins("rule", args.steps)
        return 0 if ok1 and ok2 else 1
    if args.cmd == "backtest":
        settings = settings_from(args)
        if settings.world in {"stage0", "rule", "market"}:
            settings.world = "replay"
        settings.fast = True
        if not settings.steps:
            settings.steps = 400
        if settings.out == "runs/paper":
            settings.out = "runs/backtest"
        _run(settings, dashboard=not args.no_dashboard)
        return 0
    _run(settings_from(args), dashboard=not args.no_dashboard)
    return 0
