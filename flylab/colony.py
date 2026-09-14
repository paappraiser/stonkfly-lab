from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from .config import Settings
from .decoder import HysteresisDecoder, Proposal
from .mb import FlyState, MushroomBody
from .odors import Odor, OdorEncoder


@dataclass
class ColonyStep:
    odor: Odor
    flies: list[FlyState]
    proposals: list[Proposal]
    joint: Proposal
    agreement: bool
    banner: str


class Colony:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.encoder = OdorEncoder(settings.n_pn)
        self.flies = [MushroomBody(settings, name=f"fly-{i}", seed=settings.seed + 17 * i) for i in range(settings.n_flies)]
        explore = float(getattr(settings, "explore", 0.15))
        self.decoders = [HysteresisDecoder(settings.decoder_threshold, settings.decoder_hysteresis, seed=settings.seed + 31 * (i + 1), explore=explore) for i in range(len(self.flies))]
        self.last_sides = ["HOLD"] * len(self.flies)
        self.banner = "HOLD"
        if getattr(settings, "clone_weights", False) and len(self.flies) > 1:
            src = self.flies[0]
            for fly in self.flies[1:]:
                fly.pn_to_kc = src.pn_to_kc.copy()
                fly.w_buy = src.w_buy.copy()
                fly.w_sell = src.w_sell.copy()
                fly.w_buy0 = src.w_buy0.copy()
                fly.w_sell0 = src.w_sell0.copy()

    def perceive(self, *, ret: float, vol: float, position_qty: float, planted: str | None = None) -> Odor:
        partner = self.last_sides[0] if self.last_sides else "HOLD"
        if planted:
            return self.encoder.planted(planted)
        return self.encoder.encode(ret=ret, vol=vol, position_qty=position_qty, partner_side=partner, include_partner=self.settings.partner_channel and len(self.flies) > 1)

    def decide(self, odor: Odor) -> ColonyStep:
        states, proposals = [], []
        for fly, decoder in zip(self.flies, self.decoders):
            state = fly.step(odor.vector)
            proposals.append(decoder.decode(state.score))
            states.append(state)
        self.last_sides = [p.side for p in proposals]
        joint, agreed = self._combine(proposals)
        return ColonyStep(odor, states, proposals, joint, agreed, self.banner)

    def _combine(self, proposals: list[Proposal]):
        if not proposals:
            return Proposal("HOLD", 0.0, 0.0), True
        if self.settings.colony == "solo" or len(proposals) == 1:
            return proposals[0], True
        sides = {p.side for p in proposals}
        mean = sum(p.score for p in proposals) / len(proposals)
        if self.settings.colony == "soft":
            signs = [1 if s > 0.01 else -1 if s < -0.01 else 0 for s in [p.score for p in proposals]]
            if -1 in signs and 1 in signs:
                return Proposal("HOLD", mean, abs(mean)), False
            if 1 in signs:
                return Proposal("BUY", mean, abs(mean)), True
            if -1 in signs:
                return Proposal("SELL", mean, abs(mean)), True
            return Proposal("HOLD", mean, abs(mean)), False
        if len(sides) == 1:
            return Proposal(proposals[0].side, mean, abs(mean)), True
        return Proposal("HOLD", mean, abs(mean)), False

    def reinforce_all(self, snapshots: list, valence: float) -> None:
        if self.settings.shuffle_reward:
            valence = -valence
        for fly, elig in zip(self.flies, snapshots):
            fly.reinforce(elig, valence)

    def snapshots(self):
        return [fly.snapshot_eligibility() for fly in self.flies]

    def save_brains(self, path) -> None:
        Path(path).write_text(json.dumps([fly.dump() for fly in self.flies]))

    def load_brains(self, path) -> None:
        p = Path(path)
        if p.exists():
            payload = json.loads(p.read_text())
            for fly, blob in zip(self.flies, payload):
                fly.load(blob)
