const $ = (id) => document.getElementById(id);
const QUIPS = {
  BUY: ["BUY. The blob grew. The blob must be collected.", "Antennae say green goo. Deploy the paper dollars.", "Both compound eyes agree: yeet cash at it."],
  SELL: ["SELL. Put the shiny rocks back in the jar.", "The looming disc looked angry. Evict the bag.", "Aversive juice. We would like to not be here."],
  HOLD: ["HOLD. Two flies, zero consensus, maximum dignity.", "Sitting very still. This is also a strategy. Allegedly.", "Sniffing continues. Trading does not."],
  FLATTEN: ["FLATTEN. The halt horn went off. Dump the inventory.", "Risk bug ate the trading bug. Out."],
};
function quip(side, step) { const pack = QUIPS[side] || QUIPS.HOLD; return pack[step % pack.length]; }
function drawCurve(points) {
  const canvas = $("curve"); if (!canvas) return;
  const ctx = canvas.getContext("2d"); const w = canvas.width, h = canvas.height;
  ctx.clearRect(0, 0, w, h); if (!points || points.length < 2) return;
  const ys = points.map((p) => p[1]); const min = Math.min(...ys); const max = Math.max(...ys);
  const span = Math.max(max - min, 0.01);
  ctx.strokeStyle = "#7dffb3"; ctx.lineWidth = 3; ctx.beginPath();
  points.forEach((p, i) => {
    const x = (i / (points.length - 1)) * (w - 8) + 4;
    const y = h - 8 - ((p[1] - min) / span) * (h - 16);
    if (i === 0) ctx.moveTo(x, y); else ctx.lineTo(x, y);
  });
  ctx.stroke();
}
function flyCard(fly, proposal) {
  const side = proposal ? proposal.side : "HOLD";
  const drift = Math.min(100, Math.abs(fly.weight_drift) * 80);
  return `<div class="fly"><b>🪰 ${fly.name}</b><div class="side-${side}">${side} · score ${fly.score.toFixed(3)}</div><div class="sub">sparsity ${(fly.sparsity * 100).toFixed(1)}% of KCs lit</div><div class="sub">memory drift ${fly.weight_drift.toFixed(3)}</div><div class="bar"><span style="width:${drift}%"></span></div></div>`;
}
async function tick() {
  try {
    const data = await (await fetch("/api/state", { cache: "no-store" })).json();
    const ev = data.event; if (!ev) return;
    const mid = Number(ev.mid);
    $("tagline").textContent = ev.halted ? "the floor manager pulled the plug" : "two bugs watching a number go brr";
    $("world").textContent = `world ${data.settings.world}`;
    $("colony").textContent = `${data.settings.colony} · ${data.settings.n_flies} fly`;
    $("halt").textContent = ev.halted ? `HALT · ${ev.halt_reason}` : "still buzzing";
    $("halt").classList.toggle("halt", !!ev.halted);
    $("equity").textContent = `$${Number(ev.equity).toFixed(2)}`;
    $("book").textContent = `cash ${Number(ev.cash).toFixed(2)} · qty ${Number(ev.qty).toFixed(6)} · fee ${data.settings.fee_bps} bp`;
    const start = data.equity_curve && data.equity_curve[0] ? data.equity_curve[0][1] : 100;
    const pnl = Number(ev.equity) - start;
    $("pnl").textContent = `P&L vs first mark ${pnl >= 0 ? "+" : ""}${pnl.toFixed(2)}  ·  step ${ev.step}`;
    $("joint").textContent = ev.executed;
    $("joint").className = `big side-${ev.executed}`;
    $("reason").textContent = `${ev.reason} · decoder wanted ${ev.joint.side}`;
    $("speech").textContent = quip(ev.executed, ev.step);
    $("odor").textContent = ev.odor;
    $("labels").textContent = ev.labels ? Object.entries(ev.labels).map(([k, v]) => `${k}:${v}`).join("   ") : "";
    const m = ev.metrics || {}; const total = (m.agreements || 0) + (m.disagreements || 0);
    $("agree").textContent = ev.agreement ? "YES 🤝" : "NOPE";
    $("agree-stats").textContent = `${total ? (100 * m.agreements / total).toFixed(0) : "—"}% of ticks matched · ${m.fills || 0} fills`;
    if (ev.stage0_acc == null) { $("acc").textContent = "n/a"; $("target").textContent = "live-ish market world — no planted answer"; }
    else { $("acc").textContent = `${(100 * ev.stage0_acc).toFixed(0)}%`; $("target").textContent = `teacher wanted ${ev.stage0_target || "—"} · n=${m.stage0_decisions}`; }
    $("flies").innerHTML = (ev.flies || []).map((f, i) => flyCard(f, (ev.proposals || [])[i])).join("");
    drawCurve(data.equity_curve || []);
    $("frame").src = "/api/frame?t=" + ev.step;
    $("ticker").textContent = `step ${ev.step}   ${ev.product} ${mid.toFixed(2)}   odor ${ev.odor}   joint ${ev.executed}   equity $${Number(ev.equity).toFixed(2)}   agree ${ev.agreement ? "yes" : "no"}   fills ${m.fills || 0}`;
  } catch (err) {
    $("tagline").textContent = "engine is still putting its tiny shoes on";
  }
}
tick(); setInterval(tick, 1000);
