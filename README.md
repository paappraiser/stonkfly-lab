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

## Install

Python 3.11+. WSL users: put the clone on `E:` as `/mnt/e/stonkfly` if `C:` is full.

```bash
git clone https://github.com/paappraiser/stonkfly-lab.git
cd stonkfly-lab
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
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
`demo` with two flies in old `agree` mode reports ~0% joint accuracy because HOLD is never the planted answer. Current `demo` is one fly.

### Just run it

```bash
# live paper BTC, two flies, softer veto
python -m flylab run --world market --colony soft --flies 2 --interval 15 --out runs/paper

# one fly, no committee
python -m flylab run --world market --colony solo --flies 1 --interval 15 --out runs/solo

# fast candle replay
python -m flylab backtest --colony soft --flies 2 --steps 400 --out runs/backtest

# watch Stage 0 slowly with the dashboard
python -m flylab run --world stage0 --colony solo --flies 1 --interval 1 --out runs/watch
```

Open [http://127.0.0.1:7474](http://127.0.0.1:7474) **while the process is running**. Stop with Ctrl-C or `touch runs/paper/STOP`.

A `BrokenPipeError` from the dashboard is the browser dropping a frame. The fly is still ticking.

### Worlds

| `--world` | Tape | Teacher |
|---|---|---|
| `stage0` | planted smell A=BUY, B=SELL | yes — $0.80 juice per correct yell |
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
| `soft` | Same **sign** of score is enough. HOLD+BUY can become BUY. Opposite signs sit. |
| `governor` | Fly-0 paints a banner; the scout may only go that way or sit. |

`--clone` copies fly-0 wiring onto the others so `agree` fires more often. That is one brain with two name tags, not two students.

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
--no-dashboard
--fee-bps 8
--product BTC-USD
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
