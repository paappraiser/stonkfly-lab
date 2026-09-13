# Design notes

## Why this exists

[stonkfly](https://github.com/nftechie/stonkfly) is the real connectome experiment. Its learning path is blocked in three places at once: the chart barely drives Kenyon cells, dopamine grades portfolio weather instead of the last action, and the plastic synapses do not drive the decoder.

This lab isolates those three variables in a model small enough to run while you watch a dashboard.

## Memory rule

Each fly:

1. Expands a 32-dim odor into 800 sparse KCs (top-k, ~8% active).
2. Reads two MBON pools (buy vs sell).
3. Stores an eligibility trace of the KC pattern at decision time.
4. On the next step, applies a three-factor update:

   - profit: potentiate KC→buy, depress KC→sell
   - loss: the opposite
   - magnitude clipped to `[-1, 1]` and scaled by `|\u0394equity| / order_notional` in the market world

Weights decay toward their birth values and stay inside `[0.1, 2]\u00d7` baseline.

This is *not* a reproduction of Huang, Luo et al. 2024. It is the smallest rule that can pass Stage 0 and still look like an MB.

## Stage 0

Pattern A is a PN burst on the high end of the `move` bundle and is rewarded only after BUY. Pattern B is the low end and is rewarded only after SELL. HOLD is a mild slap.

Pass: plastic accuracy \u226b frozen and shuffled from the same seed.

## Market world

Public Coinbase ticker + 1-minute history for features. Fills are paper, marked at bid/ask with a configurable fee. Reward is delayed one observation and can ignore the fee so the first clip is not automatically aversive.

Guard:

- $20 lifetime hole → halt
- $8 daily hole → halt
- optional flatten on halt (default on)
- max hold of 24 steps
- no shorts

## Two flies

Different seeds → different PN\u2192KC wiring. Each can smell the other's last side as a `partner` odor. Joint action is agree-or-sit. Concordance and counterfactual solo policies are the measurements that matter, not a lucky equity tick.
