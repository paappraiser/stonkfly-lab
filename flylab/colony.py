from __future__ import annotations

from dataclasses import dataclass

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
        self.flies = [
            MushroomBody(settings, name=f"fly-{i}", seed=settings.seed + 17 * i)
            for i in range(settings.n_flies)
        ]
        self.decoders = [
            HysteresisDecoder(
                settings.decoder_threshold,
                settings.decoder_hysteresis,
                seed=settings.seed + 31 * (i + 1),
                explore=0.25 if settings.world == "stage0" else 0.08,
            )
            for i in range(len(self.flies))
        ]
        self.last_sides = ["HOLD"] * len(self.flies)
        self.banner = "HOLD"
        self.governor_clock = 0

    def perceive(self, *, ret: float, vol: float, position_qty: float, planted: str | None = None) -> Odor:
        partner = self.last_sides[0] if self.last_sides else "HOLD"
        if planted:
            return self.encoder.planted(planted)
        return self.encoder.encode(
            ret=ret,
            vol=vol,
            position_qty=position_qty,
            partner_side=partner,
            include_partner=self.settings.partner_channel and len(self.flies) > 1,
        )

    def decide(self, odor: Odor) -> ColonyStep:
        states = []
        proposals = []
        for fly, decoder in zip(self.flies, self.decoders):
            state = fly.step(odor.vector)
            proposal = decoder.decode(state.score)
            states.append(state)
            proposals.append(proposal)
        self.last_sides = [p.side for p in proposals]
        joint, agreed = self._combine(proposals)
        if self.settings.colony == "governor" and self.flies:
            self.governor_clock += 1
            if self.governor_clock % 4 == 0:
                self.banner = proposals[0].side
        return ColonyStep(odor, states, proposals, joint, agreed, self.banner)

    def _combine(self, proposals: list[Proposal]) -> tuple[Proposal, bool]:
        if not proposals:
            return Proposal("HOLD", 0.0, 0.0), True
        if self.settings.colony == "solo" or len(proposals) == 1:
            return proposals[0], True
        if self.settings.colony == "governor":
            scout = proposals[-1]
            if self.banner == "HOLD":
                return scout, True
            if scout.side == "HOLD" or scout.side == self.banner:
                return scout if scout.side != "HOLD" else Proposal(self.banner, scout.score, scout.confidence), True
            return Proposal("HOLD", scout.score, scout.confidence), False
        sides = {p.side for p in proposals}
        if len(sides) == 1:
            mean = sum(p.score for p in proposals) / len(proposals)
            return Proposal(proposals[0].side, mean, abs(mean)), True
        mean = sum(p.score for p in proposals) / len(proposals)
        return Proposal("HOLD", mean, abs(mean)), False

    def reinforce_all(self, snapshots: list, valence: float) -> None:
        if self.settings.shuffle_reward:
            valence = -valence
        for fly, elig in zip(self.flies, snapshots):
            fly.reinforce(elig, valence)

    def snapshots(self) -> list:
        return [fly.snapshot_eligibility() for fly in self.flies]
