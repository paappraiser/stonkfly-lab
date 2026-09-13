# Stonkfly Lab

A laptop-sized experiment inspired by [nftechie/stonkfly](https://github.com/nftechie/stonkfly).

This is **not** the 166,700-neuron MaleCNS graph. That simulator needs a C++ kernel, ~16 GB RAM, and a 1.1 GB download. This repo keeps the *circuit motif* that actually learns in a fly — sparse Kenyon cells, plastic KC→MBON synapses, dopamine-gated updates — and wires it the way a trading experiment can use:

- market state as **virtual odors**, not a candlestick screenshot
- **delayed** dopamine on the action that was just taken
- readout from the **MBONs you modify**, with hysteresis
- one or two flies, **agree-or-sit**
- paper BTC from Coinbase public data
- a live dashboard on `http://127.0.0.1:7474`

Profitable trading has not been demonstrated. Stage 0 (planted odors) *should* learn. That is the point: if Stage 0 fails, the market run is theater.

## Install

Python 3.11+.

```bash
git clone https://github.com/paappraiser/stonkfly-lab.git
cd stonkfly-lab
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -e '.[test]'
python -m flylab doctor
```

## Run it

**1. Prove the wire (do this first)**

```bash
python -m flylab demo
```

Opens [http://127.0.0.1:7474](http://127.0.0.1:7474). Two well-separated odors are paired with BUY and SELL. Accuracy should climb well above chance. Then:

```bash
python -m flylab twins
```

Plastic must beat frozen weights and shuffled dopamine. If it does not, stop. The market cannot teach a broken memory rule.

**2. Paper BTC, still fake fills**

```bash
python -m flylab run --world market --colony agree --flies 2 --interval 15
```

Uses Coinbase public BTC-USD prints. Starts with $100 paper cash, $10 clips, 8 bp fees, flatten-on-halt at a $20 drawdown. Ctrl-C stops. `touch runs/paper/STOP` also stops. Resume by running the same command — ledger and run dir persist.

Offline stand-in if you have no network:

```bash
python -m flylab run --world fixture --fast --steps 200
```

**3. Controls**

```bash
python -m flylab run --world market --frozen --out runs/frozen
python -m flylab run --world market --shuffle-reward --out runs/shuffled
```

A green plastic run that frozen also prints is just BTC going up.

## What changed vs looking at a chart

Stonkfly feeds a 320×180 RGB candle chart into photoreceptors. Most Kenyon cells never see that picture. The synapses it changes are the mushroom-body association table, whose native conditioned stimulus is an **odor**.

This lab maps:

| market fact | odor factor |
|---|---|
| last return | `move`: down_strong…up_strong |
| recent vol | `vol`: calm / normal / wild |
| inventory | `pos`: flat / long / short |
| other fly's last call | `partner`: hold / buy / sell |

The dashboard still draws a motion pane (looming disc + ribbon) so you have something to watch. That image is spectator UI. The brain eats the odor vector.

## Colony modes

- `solo` — one fly, its MBON score is the order
- `agree` — two flies, different random KC wiring; trade only when they match
- `governor` — fly-0 tints a banner every 4 steps; fly-1 is the scout

## Honest limits

- Paper broker only. There is no Coinbase order button in this repo.
- Compact MB (800 KCs), not MaleCNS.
- Delayed one-step mark-to-market is still a crude teacher.
- Fees, halt-with-flatten, and time-stops exist so a laptop session cannot quietly sit in a bag after a 20% hole.
- If you want the full fly, keep running `nftechie/stonkfly` in paper mode and treat this lab as the place you test encoding + credit assignment.

## Layout

```
flylab/           engine, MB, odors, broker, dashboard
flylab/web/       live UI
tests/            stage-0 and broker checks
docs/DESIGN.md    why these choices
```

MIT. Not affiliated with Coinbase or the MaleCNS collaboration.
