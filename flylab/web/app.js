const $ = (id) => document.getElementById(id);
const QUIPS = {
  BUY: ["BUY. The blob grew. The blob must be collected.", "Antennae say green goo. Deploy the paper dollars.", "Both compound eyes agree: yeet cash at it."],
  SELL: ["SELL. Put the shiny rocks back in the jar.", "The looming disc looked angry. Evict the bag.", "Aversive juice. We would like to not be here."],
  HOLD: ["HOLD. Two flies, zero consensus, maximum dignity.", "Sitting very still. This is also a strategy. Allegedly.", "Sniffing continues. Trading does not."],
  FLATTEN: ["FLATTEN. The halt horn went off. Dump the inventory.", "Risk bug ate the trading bug. Out."],
};
const GLOM_ORDER = ["move", "vol", "pos", "partner"];
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
function drawPn(vec) {
  const canvas = $("pn-bars"); if (!canvas) return;
  const ctx = canvas.getContext("2d"); const w = canvas.width, h = canvas.height;
  ctx.clearRect(0, 0, w, h); if (!vec || !vec.length) return;
  const n = vec.length, gap = 2, bw = Math.max(2, (w - 8) / n - gap);
  vec.forEach((v, i) => {
    const amp = Math.max(0, Math.min(1, Number(v) || 0));
    ctx.fillStyle = amp > 0.2 ? "#ffb347" : "#3a2418";
    ctx.fillRect(4 + i * (bw + gap), h - 4 - amp * (h - 10), bw, amp * (h - 10));
  });
}
function renderGloms(labels) {
  const host = $("glomeruli"); if (!host) return;
  const labs = labels || {};
  host.innerHTML = GLOM_ORDER.map((k) => {
    const v = labs[k] || "—";
    return `<div class="glom ${v && v !== "—" ? "on" : ""}"><div class="gname">${k}</div><div class="gval">${v}</div></div>`;
  }).join("");
}
function renderTape(log) {
  const host = $("odor-tape"); if (!host) return;
  host.innerHTML = (log || []).slice(-24).map((r) => {
    const lab = r.labels ? (r.labels.move || r.name) : r.name;
    return `<span class="chip ${r.executed || ""}" title="${r.name}">${lab}→${r.executed || "?"}</span>`;
  }).join("");
}
function renderMemory(flies) {
  const host = $("memory"); if (!host) return;
  host.innerHTML = (flies || []).map((f) => {
    const cells = (f.kc_preview || []).map((v) => {
      const a = Math.max(0, Math.min(1, Number(v) || 0));
      return `<i style="background:rgba(125,255,179,${0.15 + a * 0.85})"></i>`;
    }).join("");
    const bs = Number(f.buy_shift || 0), ss = Number(f.sell_shift || 0);
    return `<div class="mem"><b>🪰 ${f.name}</b><div class="kc-row">${cells || "<i></i>"}</div><div class="shift"><span>BUY memory <b class="side-BUY">${bs >= 0 ? "+" : ""}${bs.toFixed(3)}</b></span><span>SELL memory <b class="side-SELL">${ss >= 0 ? "+" : ""}${ss.toFixed(3)}</b></span></div></div>`;
  }).join("");
}
function renderTips(ev, settings) {
  const host = $("tips"); if (!host) return;
  const flies = ev.flies || [];
  const drift = flies.reduce((s, f) => s + Math.abs(f.weight_drift || 0), 0) / Math.max(flies.length, 1);
  const sparse = flies.reduce((s, f) => s + (f.sparsity || 0), 0) / Math.max(flies.length, 1);
  const log = ev.odor_log || [];
  const unique = new Set(log.map((r) => r.name)).size;
  const m = ev.metrics || {};
  const total = (m.agreements || 0) + (m.disagreements || 0);
  const frozen = !!(settings && settings.frozen);
  const tips = [];
  if (ev.stage0_acc != null) tips.push([ev.stage0_acc > 0.7 ? "ok" : "bad", ev.stage0_acc > 0.7 ? "Stage 0 accuracy is high. The wire can latch a smell." : "Stage 0 accuracy is weak. Run twins before BTC."]);
  else tips.push(["meh", "No planted answer on this tape. Compare plastic vs --frozen."]);
  if (frozen) tips.push(["meh", "Frozen run. Drift should stay ~0."]);
  else if (drift < 0.01 && (ev.step || 0) > 30) tips.push(["bad", "Weights barely moved. Dopamine is 0 or HOLD ate every tick."]);
  else if (drift > 0.02) tips.push(["ok", "Memory is moving (drift " + drift.toFixed(3) + "). Frozen should stay flat."]);
  if (sparse > 0.18) tips.push(["bad", "Kenyon cells flooding. Collapse the odor alphabet."]);
  else if (sparse > 0 && sparse < 0.15) tips.push(["ok", "Sparsity looks fly-like (~" + (100 * sparse).toFixed(1) + "% KCs lit)."]);
  if (log.length > 8 && unique <= 2) tips.push(["meh", "Only " + unique + " distinct smells. Memory has nothing new to file."]);
  if (total > 20 && settings && settings.colony === "agree" && m.agreements / total < 0.05) tips.push(["meh", "Agree-or-sit never matches. Try --colony soft or solo."]);
  if (Math.abs(ev.last_valence || 0) < 1e-9 && (ev.step || 0) > 10 && !frozen) tips.push(["meh", "Last dopamine was 0. No lesson this tick."]);
  tips.push(["meh", "Improve memory: cleaner odors, delay juice on the last action only, action-conditioned SELL, lower η if weights thrash, twins on a held-out week."]);
  host.innerHTML = tips.map(([k, t]) => `<li class="${k}">${t}</li>`).join("");
  const verdict = $("learn-verdict");
  if (verdict) verdict.textContent = frozen ? "frozen twin — memory should not crawl" : drift < 0.01 ? "synapses quiet" : "synapses crawling · drift " + drift.toFixed(3);
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
    const on = $("odor-name"); if (on) on.textContent = ev.odor || "—";
    renderGloms(ev.labels); drawPn(ev.odor_vector); renderTape(ev.odor_log); renderMemory(ev.flies); renderTips(ev, data.settings);
    const m = ev.metrics || {}; const total = (m.agreements || 0) + (m.disagreements || 0);
    $("agree").textContent = ev.agreement ? "YES 🤝" : "NOPE";
    $("agree-stats").textContent = `${total ? (100 * m.agreements / total).toFixed(0) : "—"}% of ticks matched · ${m.fills || 0} fills`;
    if (ev.stage0_acc == null) { $("acc").textContent = "n/a"; $("target").textContent = "live-ish market world — no planted answer"; }
    else { $("acc").textContent = `${(100 * ev.stage0_acc).toFixed(0)}%`; $("target").textContent = `teacher wanted ${ev.stage0_target || "—"} · n=${m.stage0_decisions}`; }
    $("flies").innerHTML = (ev.flies || []).map((f, i) => flyCard(f, (ev.proposals || [])[i])).join("");
    drawCurve(data.equity_curve || []);
    $("frame").src = "/api/frame?t=" + ev.step;
    $("ticker").textContent = `step ${ev.step}   ${ev.product} ${mid.toFixed(2)}   odor ${ev.odor}   joint ${ev.executed}   equity $${Number(ev.equity).toFixed(2)}`;
  } catch (err) {
    $("tagline").textContent = "engine is still putting its tiny shoes on";
  }
}
tick(); setInterval(tick, 1000);
