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
        sp.add_argument("--world", choices=["stage0", "market", "fixture"], default="stage0")
        sp.add_argument("--colony", choices=["solo", "agree", "governor"], default="agree")
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

    run = sub.add_parser("run", help="run the experiment loop")
    add_shared(run)
    demo = sub.add_parser("demo", help="fast stage-0 proof that the wire can learn")
    demo.add_argument("--steps", type=int, default=250)
    demo.add_argument("--out", default="runs/demo")
    demo.add_argument("--port", type=int, default=7474)
    sub.add_parser("doctor", help="quick self-check")
    twins = sub.add_parser("twins", help="plastic vs frozen vs shuffled on stage0")
    twins.add_argument("--steps", type=int, default=200)
    return p


def settings_from(args: argparse.Namespace) -> Settings:
    world = getattr(args, "world", "stage0")
    return Settings(
        world=world,
        colony=getattr(args, "colony", "agree"),
        n_flies=getattr(args, "flies", 2),
        product=getattr(args, "product", "BTC-USD"),
        steps=getattr(args, "steps", 0),
        fast=bool(getattr(args, "fast", False) or world == "stage0"),
        frozen=bool(getattr(args, "frozen", False)),
        shuffle_reward=bool(getattr(args, "shuffle_reward", False)),
        out=getattr(args, "out", "runs/paper"),
        interval_seconds=getattr(args, "interval", 15.0),
        fee_bps=getattr(args, "fee_bps", 8.0),
        dashboard_port=getattr(args, "port", 7474),
        seed=getattr(args, "seed", 7),
    )


def _run(settings: Settings, dashboard: bool) -> Engine:
    engine = Engine(settings)
    if dashboard:
        serve(settings.dashboard_host, settings.dashboard_port, settings.run_dir())
        print(f"dashboard  http://{settings.dashboard_host}:{settings.dashboard_port}")
    print(f"world={settings.world} colony={settings.colony} flies={settings.n_flies} out={settings.out}")
    engine.run()
    return engine


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.cmd == "doctor":
        from .mb import MushroomBody
        from .odors import OdorEncoder
        s = Settings()
        enc = OdorEncoder(s.n_pn)
        fly = MushroomBody(s, "doc", 1)
        sa, sb = fly.step(enc.planted("A").vector), fly.step(enc.planted("B").vector)
        overlap = float(((sa.kc > 0) & (sb.kc > 0)).mean())
        print("ok  KCs", s.n_kc, "PNs", s.n_pn)
        print("ok  planted A vs B sparsity", round(sa.sparsity, 3), round(sb.sparsity, 3), "overlap", round(overlap, 3))
        print("ok  run: python -m flylab demo")
        return 0
    if args.cmd == "demo":
        settings = Settings(world="stage0", colony="agree", n_flies=2, steps=args.steps, fast=True, out=args.out, dashboard_port=args.port)
        engine = _run(settings, dashboard=True)
        acc = engine.metrics["correct_stage0"] / max(engine.metrics["stage0_decisions"], 1)
        print(f"stage0 accuracy {acc:.1%} over {engine.metrics['stage0_decisions']} decisions")
        print("This is a planted association, not market edge.")
        return 0 if acc > 0.6 else 1
    if args.cmd == "twins":
        results = {}
        for name, frozen, shuffle, out in (("plastic", False, False, "runs/twin-plastic"), ("frozen", True, False, "runs/twin-frozen"), ("shuffled", False, True, "runs/twin-shuffled")):
            s = Settings(world="stage0", colony="solo", n_flies=1, steps=args.steps, fast=True, frozen=frozen, shuffle_reward=shuffle, out=out, seed=7)
            engine = Engine(s)
            engine.run()
            acc = engine.metrics["correct_stage0"] / max(engine.metrics["stage0_decisions"], 1)
            results[name] = acc
            print(f"{name:10}  acc={acc:.1%}")
        Path("runs").mkdir(parents=True, exist_ok=True)
        Path("runs/twins.json").write_text(json.dumps(results, indent=2))
        if results["plastic"] > results["frozen"] and results["plastic"] > results["shuffled"]:
            print("pass  plastic beat frozen and shuffled on planted odors")
            return 0
        print("fail  memory rule did not beat controls")
        return 1
    _run(settings_from(args), dashboard=not args.no_dashboard)
    return 0
