from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


@dataclass
class Settings:
    product: str = "BTC-USD"
    starting_cash: float = 100.0
    order_notional: float = 10.0
    fee_bps: float = 8.0
    loss_stop: float = 20.0
    daily_loss_cap: float = 8.0
    max_hold_steps: int = 24
    flatten_on_halt: bool = True
    interval_seconds: float = 15.0
    max_quote_age: float = 30.0
    n_kc: int = 800
    n_pn: int = 32
    kc_inputs: int = 6
    n_mbon_buy: int = 4
    n_mbon_sell: int = 4
    sparsity_target: float = 0.08
    eta: float = 0.25
    weight_min: float = 0.05
    weight_max: float = 4.0
    memory_decay: float = 0.001
    eligibility_decay: float = 0.25
    decoder_threshold: float = 0.02
    decoder_hysteresis: float = 0.01
    n_flies: int = 2
    colony: str = "agree"
    clone_weights: bool = False
    partner_channel: bool = True
    world: str = "market"
    horizon_steps: int = 4
    deadband: float = 0.02
    exclude_fees_from_reward: bool = True
    proportional_dopamine: bool = True
    shuffle_reward: bool = False
    frozen: bool = False
    seed: int = 7
    out: str = "runs/paper"
    dashboard_host: str = "127.0.0.1"
    dashboard_port: int = 7474
    steps: int = 0
    fast: bool = False

    def signature(self) -> dict[str, Any]:
        return asdict(self)

    def run_dir(self) -> Path:
        path = Path(self.out)
        path.mkdir(parents=True, exist_ok=True)
        return path
