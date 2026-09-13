# Stonkfly Lab

```
       \\   /
        \\_/
     .-'     '-.
    /  (o) (o)  \      two bugs.
    |     ^     |      one paper book.
    \\   '-'   /      zero licenses.
     '-.___,-'
        | |
     paper BTC goes in
     dopamine juice comes out
```

A laptop-sized, slightly unhinged experiment inspired by
[nftechie/stonkfly](https://github.com/nftechie/stonkfly).

This is **not** the 166,700-neuron MaleCNS graph. That one needs a C++ kernel,
about 16 GB of RAM, and a 1.1 GB download. This repo keeps the *circuit motif*
that actually learns in a fly — sparse Kenyon cells, plastic KC→MBON synapses,
dopamine-gated updates — and wires it so a trading experiment can use it:

- market state as **virtual odors**, not a candlestick screenshot
- **delayed** dopamine on the action that was just taken
- readout from the **MBONs you modify**, with hysteresis
- one or two flies, **agree-or-sit**
- paper BTC from Coinbase public data
- a live dashboard that looks like a dive bar for insects: `http://127.0.0.1:7474`

Profitable trading has not been demonstrated. Stage 0 (planted odors) *should*
learn. That is the whole point. If Stage 0 fails, the market run is cosplay.

## Install

Python 3.11+.

```bash
git clone https://github.com/paappraiser/stonkfly-lab.git
cd stonkfly-lab
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -e '.[test]'
python -m flylab doctor
python -m pytest -q
```

`doctor` just checks that planted odor A and odor B light different Kenyon cells.
If they overlap a lot, the memory has nothing to grab.

## Run it

### 1. Prove the wire

```bash
python -m flylab demo
```

Opens [http://127.0.0.1:7474](http://127.0.0.1:7474).

Two well-separated smells. Pattern A is supposed to mean BUY. Pattern B is
supposed to mean SELL. Dopamine arrives on the *next* tick, bound to the Kenyon
pattern from the decision tick. Accuracy should climb well above a coin flip.

Then run the controls:

```bash
python -m flylab twins
```

You want something in this shape:

```
plastic     acc=82%
frozen      acc=51%
shuffled    acc=48%
pass  plastic beat frozen and shuffled on planted odors
```

If plastic cannot beat those two, stop. BTC will not save you.

### 2. Paper BTC, still fake fills

```bash
python -m flylab run --world market --colony agree --flies 2 --interval 15
```

Uses Coinbase public BTC-USD prints. Starts with $100 paper cash, $10 clips,
8 bp fees, flatten-on-halt at a $20 drawdown.

No network:

```bash
python -m flylab run --world fixture --fast --steps 200
```

Stop with Ctrl-C or `touch runs/paper/STOP`. Same command resumes the ledger.

### 3. Controls on the same tape

```bash
python -m flylab run --world market --frozen --out runs/frozen
python -m flylab run --world market --shuffle-reward --out runs/shuffled
```

A green plastic run that frozen also prints is just BTC going up.

## What one tick actually does

```
price / inventory / partner vote
            |
            v
     virtual odor   (32 projection-neuron channels)
            |
            v
     800 Kenyon cells, ~8% lit
            |
            v
     buy MBONs vs sell MBONs  ->  score  ->  BUY / SELL / HOLD
            |
            v
     two flies? only trade if they match
            |
            v
     paper broker (or stage-0 teacher)
            |
            v
     NEXT tick: dopamine hits the KC pattern from THIS tick
```

That last arrow is the whole upgrade versus "look at a chart and hope."

## How to read the dashboard

| Thing on screen | What it is | What "good" looks like |
|---|---|---|
| Paper pile | cash + inventory marked at mid | not the score that matters |
| Spectator eyeball | looming disc + price ribbon | ignore for learning; it is theater |
| What they did | executed side after the guard | BUY/SELL should not be 100% one way |
| Odor | `move|vol|pos|partner` | should change when the market changes |
| Agreement | both flies same side | not 0%, not 100% forever |
| Stage 0 report card | % correct vs planted teacher | climb past ~70% in the demo |
| sparsity | fraction of KCs on | around 8%; a flood is bad |
| drift | weight change from birth | frozen twin stays ~0 |

Speech bubbles are jokes. The numbers are not.

## The odor alphabet

The mushroom body in a real fly mostly learns **smells**, not screenshots.
So the market is encoded as a small odor:

| Factor | Bins | Meaning |
|---|---|---|
| `move` | down_strong … up_strong | last return |
| `vol` | calm / normal / wild | recent wiggliness |
| `pos` | flat / long / short | are we already in the bag? |
| `partner` | hold / buy / sell | what the other fly just yelled |

Nearby bins overlap a little, like similar smells. Planted Stage 0 uses only
the far ends of `move`, so A and B barely share Kenyon cells.

## Colony modes

- `solo` — one fly, its score is the order
- `agree` — two flies, different random wiring; no match, no trade
- `governor` — fly-0 paints a banner every 4 steps; fly-1 is the scout

## Risk bugs (the boring ones that save you)

- $20 lifetime hole → halt
- $8 daily hole → halt
- flatten-on-halt is on by default
- max hold 24 steps
- no shorts
- paper only. There is no Coinbase order button in this repo

## Honest limits

- Compact MB (800 KCs), not MaleCNS
- Delayed one-step mark-to-market is still a crude teacher
- Fees, halt, and time-stops exist so a laptop session cannot quietly sit in a bag
- If you want the full fly, keep running `nftechie/stonkfly` in paper mode and treat this lab as the place you test encoding + credit assignment

## Layout

```
flylab/           engine, MB, odors, broker, dashboard
flylab/web/       the dive-bar UI
tests/            stage-0 and broker checks
docs/DESIGN.md    why these choices, with fewer jokes
```

MIT. Not affiliated with Coinbase, Janelia, or any fly that asked to be here.
