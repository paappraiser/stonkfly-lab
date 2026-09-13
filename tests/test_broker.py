from pathlib import Path
from flylab.broker import PaperBroker
from flylab.odors import OdorEncoder, move_bin


def test_round_trip_fees(tmp_path: Path):
    b = PaperBroker(tmp_path / "l.json", cash=100, fee_bps=10)
    fill = b.market_order("BUY", 10, bid=99, ask=100)
    assert fill is not None
    assert b.qty > 0
    assert b.cash < 90.1
    sell = b.market_order("SELL", 10, bid=99, ask=100)
    assert sell is not None
    assert b.qty == 0
    assert b.equity(100) < 100


def test_move_bins_are_ordered():
    assert move_bin(-0.02) < move_bin(0.0) < move_bin(0.02)
    enc = OdorEncoder(32)
    assert (enc.planted("A").vector * enc.planted("B").vector).sum() == 0
