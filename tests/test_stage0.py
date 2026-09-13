from flylab.config import Settings
from flylab.engine import Engine
from flylab.mb import MushroomBody
from flylab.odors import OdorEncoder


def test_planted_odors_are_sparse_and_different():
    enc = OdorEncoder(32)
    fly = MushroomBody(Settings(n_kc=400, n_pn=32), "t", 3)
    a = fly.step(enc.planted("A").vector)
    b = fly.step(enc.planted("B").vector)
    assert a.sparsity < 0.2
    assert b.sparsity < 0.2
    overlap = float(((a.kc > 0) & (b.kc > 0)).mean())
    assert overlap < 0.05


def test_plastic_beats_frozen_on_stage0(tmp_path):
    common = dict(world="stage0", colony="solo", n_flies=1, steps=180, fast=True, seed=11)
    plastic = Engine(Settings(out=str(tmp_path / "plastic"), frozen=False, **common))
    frozen = Engine(Settings(out=str(tmp_path / "frozen"), frozen=True, **common))
    plastic.run()
    frozen.run()
    p = plastic.metrics["correct_stage0"] / plastic.metrics["stage0_decisions"]
    f = frozen.metrics["correct_stage0"] / frozen.metrics["stage0_decisions"]
    assert p > 0.7
    assert p > f + 0.08


def test_plastic_beats_frozen_on_rule_world(tmp_path):
    common = dict(world="rule", colony="solo", n_flies=1, steps=280, fast=True, seed=11)
    plastic = Engine(Settings(out=str(tmp_path / "plastic"), frozen=False, **common))
    frozen = Engine(Settings(out=str(tmp_path / "frozen"), frozen=True, **common))
    plastic.run()
    frozen.run()
    p = plastic.metrics["correct_stage0"] / plastic.metrics["stage0_decisions"]
    f = frozen.metrics["correct_stage0"] / frozen.metrics["stage0_decisions"]
    assert p > 0.62
    assert p > f + 0.05
