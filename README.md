# Stonkfly Lab

```
       \\   /
        \\_/
     .-'     '-.
    /  (o) (o)  \\      two bugs.
    |     ^     |      one paper book.
    \\   '-'   /      zero licenses.
     '-.___,-'
        | |
     paper BTC goes in
     dopamine juice comes out
```

A laptop-sized experiment inspired by [nftechie/stonkfly](https://github.com/nftechie/stonkfly).

This is **not** the 166,700-neuron MaleCNS graph. Compact mushroom body only:
sparse Kenyon cells, plastic KC→MBON synapses, delayed dopamine on the last action.
Dashboard: [http://127.0.0.1:7474](http://127.0.0.1:7474).

Profitable trading has not been demonstrated. Stage 0 (planted odors) should learn.
If that fails, a market run is cosplay.

## What this is based on

A fruit fly does not learn “BTC from a candlestick screenshot.” The organ that
actually associates *this stimulus* with *that outcome* is the **mushroom body**.

In the real fly it works roughly like this:

1. **Odor** hits the antennae. Projection neurons (PNs) carry a small, stable
   pattern for that smell.
2. Those PNs fan out onto a huge pile of **Kenyon cells (KCs)**. Each KC listens
   to only a few PNs, so the smell becomes a *sparse* code: only ~5–10% of KCs
   fire. Similar smells overlap a little. Different smells barely overlap.
3. Those KCs synapse onto **mushroom-body output neurons (MBONs)** — approach vs
   avoid, in the animal. Here we treat two MBON pools as BUY vs SELL.
4. **Dopamine neurons** (PAM / PPL1 families) gate plasticity at the KC→MBON
   synapse. Reward or punishment arriving *while a KC pattern is still eligible*
   changes how that smell will vote next time. That is three-factor learning:
   who fired, whether dopamine showed up, whether it was good or bad.

That circuit is an associative memory for **odors**, not a visual cortex for
candles. The fly *has* eyes. Looming and motion live in other pathways. Those
pathways do not own the KC→MBON learning rule this lab is copying.

[nftechie/stonkfly](https://github.com/nftechie/stonkfly) feeds a chart image
into photoreceptors of the full MaleCNS connectome. That is a beautiful toy.
It is also a mismatch: Kenyon cells are mostly olfactory, the decoder in that
project read a turning neuron instead of the MBONs you actually modify, and
marked-to-market juice was not bound to the action that just fired. Weights can
move and the fly can still learn nothing about price.

This lab keeps the **motif** and throws away the costume:

| Real fly | This lab |
|---|---|
| Odor on the antennae | Virtual odor from return, vol, inventory, partner vote |
| Sparse KC expansion | 800 KCs, ~8% on |
| KC→MBON synapses | Two pools: buy MBONs and sell MBONs |
| Dopamine at the right moment | Next tick, on the KC snapshot from the decision |
| Approach / avoid | BUY / SELL / HOLD |
| Chart on the retina | Dashboard PNG only. The brain does not see it. |

So the market is turned into a **smell alphabet**, not a picture:

| Factor | Bins | Meaning |
|---|---|---|
| `move` | down_strong … up_strong | last return |
| `vol` | calm / normal / wild | recent wiggliness |
| `pos` | flat / long / short | already in the bag? |
| `partner` | hold / buy / sell | what the other fly just yelled |

Nearby bins overlap a little, like similar odors. Stage 0 plants only the far
ends of `move` so smell A and smell B barely share Kenyon cells. That is why
Stage 0 can hit ~96% and live BTC two-fly `agree` can sit on HOLD all afternoon:
one is two clean smells, the other is a blurry mixtape.

The spectator eyeball on the dashboard is theater. If you find yourself watching
the looming disc to decide whether the fly is smart, you are looking at the
wrong organ.

## Install

Python 3.11+. WSL users: put the clone on `E:` as `/mnt/e/stonkfly` if `C:` is full.

```bash
git clone https://github.com/paappraiser/stonkfly-lab.git
cd stonkfly-lab
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\\Scripts\\activate
pip install -e '.[test]'
python -m flylab doctor
python -m pytest -q
```

## Usage

All commands: `python -m flylab <cmd>`.

| Command | What it does |
|---|---|
| `doctor` | Boot check. A and B must light different Kenyon cells. |
| `demo` | Fast Stage 0, one fly, dashboard. Exits after 250 ticks. |
| `twins` | Plastic vs frozen vs shuffled on a teacher world. |
| `school` | Twins on Stage 0, then twins on the rule world. |
| `run` | Leave-on loop. You pick world, colony, interval. |
| `backtest` | Fast replay of ~300 Coinbase minutes (or a fake tape). |

### Prove the wire

```bash
python -m flylab doctor
python -m flylab twins
python -m flylab twins --world rule
python -m flylab school
```

Pass looks like plastic >> frozen and shuffled (example: `96% / 0% / 0%`).

### Just run it

```bash
python -m flylab run --world market --colony soft --flies 2 --interval 15 --out runs/paper
python -m flylab run --world market --colony solo --flies 1 --interval 15 --out runs/solo
python -m flylab backtest --colony soft --flies 2 --steps 400 --out runs/backtest
python -m flylab run --world stage0 --colony solo --flies 1 --interval 1 --out runs/watch
```

Open [http://127.0.0.1:7474](http://127.0.0.1:7474) **while the process is running**.
Stop with Ctrl-C or `touch runs/paper/STOP`.

### Worlds

| `--world` | Tape | Teacher |
|---|---|---|
| `stage0` | planted smell A=BUY, B=SELL | yes — juice per correct yell |
| `rule` | same pairing, jittered return size | yes |
| `market` | live Coinbase BTC-USD | mark-to-market, fees |
| `replay` | last ~300 one-minute closes, fast | mark-to-market |
| `fixture` | offline random walk | mark-to-market |

Stage 0 / rule **print fake dollars** when accuracy is high. That is the teacher score, not profit.

### Colony

`--flies` is headcount. `--colony` is how votes become one order.

| `--colony` | Rule |
|---|---|
| `solo` | One fly. Its side is the order. |
| `agree` | All must yell the same word or HOLD. |
| `soft` | Same **sign** of score is enough. HOLD+BUY can become BUY. |
| `governor` | Fly-0 paints a banner; the scout may only go that way or sit. |

`--clone` copies fly-0 wiring onto the others. That is one brain with two name tags.
Two-fly `agree` on BTC will sit on HOLD for hours. That is the veto, not a freeze.

### Useful flags

```
--steps 0          run until STOP / Ctrl-C
--fast             no sleep between ticks
--interval 15      seconds between live ticks
--frozen           no dopamine
--shuffle-reward   flip dopamine sign (control)
--out runs/name    ledger + events.jsonl + dashboard files
--port 7475        if 7474 is busy
--clone            copy fly-0 weights onto the others
```

### Controls

```bash
python -m flylab backtest --colony soft --flies 2 --steps 400 --out runs/bt-plastic
python -m flylab backtest --colony soft --flies 2 --steps 400 --frozen --out runs/bt-frozen
```

If those two ledgers match, nothing was learned about the tape.

## How to read the dashboard

| Widget | Meaning |
|---|---|
| Paper pile | cash + mark-to-mid. Not the grade that matters on Stage 0. |
| Spectator eyeball | pretty PNG. The brain does not trade off this image. |
| What they did | executed side after colony + risk. |
| Odor | `move\|vol\|pos\|partner` |
| Agreement | did the colony match this tick? |
| sparsity | fraction of KCs lit. ~8% is healthy. |
| drift | how far weights moved from birth. Frozen stays ~0. |

## One tick

```
odor → sparse KCs → buy vs sell MBONs → colony vote
 → paper broker or teacher
 → NEXT tick: dopamine on the KC pattern from THIS tick
```

Teacher worlds flip the sign on SELL so a correct sell strengthens sell MBONs.

## Honest limits

- Compact MB (800 KCs), not MaleCNS
- Paper only. No live Coinbase orders in this repo
- Two-fly market HOLD is expected
- A rising Stage 0 equity curve is juice, not an ATM

MIT. Not affiliated with Coinbase, Janelia, or any fly that asked to be here.
