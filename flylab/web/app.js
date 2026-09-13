const $ = (id) => document.getElementById(id);
const GLOM_ORDER = ["move", "vol", "pos", "partner"];
function set(id, text) { const el = $(id); if (el) el.textContent = text; }
function renderGloms(labels) {
  const host = $("glomeruli"); if (!host) return;
  const labs = labels || {};
  host.innerHTML = GLOM_ORDER.map((k) => {
    const v = labs[k] || "—";
    return `<div class="glom ${v && v !== "—" ? "on" : ""}"><div class="gname">${k}</div><div class="gval">${v}</div></div>`;
  }).join("");
}
function drawPn(vec) {
  const canvas = $("pn-bars"); if (!canvas) return;
  const ctx = canvas.getContext("2d"); const w = canvas.width, h = canvas.height;
  ctx.clearRect(0, 0, w, h);
  if (!vec || !vec.length) return;
  const n = vec.length, gap = 2, bw = Math.max(2, (w - 8) / n - gap);
  vec.forEach((v, i) => {
    const amp = Math.max(0, Math.min(1, Number(v) || 0));
    ctx.fillStyle = amp > 0.2 ? "#ffb347" : "#3a2418";
    ctx.fillRect(4 + i * (bw + gap), h - 4 - amp * (h - 10), bw, Math.max(1, amp * (h - 10)));
  });
}
function renderTape(log) {
  const host = $("odor-tape"); if (!host) return;
  host.innerHTML = (log || []).slice(-24).map((r) => {
    const lab = (r.labels && r.labels.move) || r.name || "?";
    return `<span class="chip ${r.executed || ""}">${lab}→${r.executed || "?"}</span>`;
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
    const drift = Number(f.weight_drift || 0);
    return `<div class="mem"><b>${f.name || "fly"}</b><div class="kc-row">${cells || "<i></i>"}</div><div class="shift">BUY ${bs.toFixed(3)} · SELL ${ss.toFixed(3)} · drift ${drift.toFixed(3)}</div></div>`;
  }).join("") || "<p class=sub>no fly snapshot yet</p>";
}
function renderTips(ev, settings) {
  const host = $("tips"); if (!host) return;
  const acc = ev.stage0_acc;
  const lines = [];
  if (acc == null) lines.push("Market tape — no planted answer.");
  else if (acc > 0.7) lines.push("Stage 0 is learned. The $ pile is juice, not profit.");
  else lines.push("Stage 0 still weak.");
  lines.push("Watch BUY vs SELL memory walk opposite ways on A vs B.");
  host.innerHTML = lines.map((t) => `<li>${t}</li>`).join("");
}
async function tick() {
  try {
    const res = await fetch("/api/state", { cache: "no-store" });
    const data = await res.json();
    const ev = data.event;
    if (!ev) return;
    const s = data.settings || {};
    set("world", "world " + (s.world || "?"));
    set("colony", (s.colony || "?") + " · " + (s.n_flies || "?") + " fly");
    set("halt", ev.halted ? "HALT" : "still buzzing");
    set("equity", "$" + Number(ev.equity || 0).toFixed(2));
    set("book", "cash " + Number(ev.cash || 0).toFixed(2) + " · qty " + Number(ev.qty || 0).toFixed(6));
    set("pnl", "step " + ev.step + " — Stage 0 dollars are juice");
    set("joint", ev.executed || "HOLD");
    if ($("joint")) $("joint").className = "big side-" + (ev.executed || "HOLD");
    set("reason", ev.reason || "—");
    set("odor", ev.odor || "—");
    set("labels", ev.labels ? Object.keys(ev.labels).map((k) => k + ":" + ev.labels[k]).join("   ") : "");
    set("odor-name", ev.odor || "—");
    renderGloms(ev.labels);
    drawPn(ev.odor_vector);
    renderTape(ev.odor_log);
    renderMemory(ev.flies);
    renderTips(ev, s);
    const m = ev.metrics || {};
    set("agree", ev.agreement ? "YES" : "NOPE");
    set("agree-stats", (m.fills || 0) + " fills");
    if (ev.stage0_acc == null) { set("acc", "n/a"); set("target", "no teacher"); }
    else { set("acc", (100 * ev.stage0_acc).toFixed(0) + "%"); set("target", "teacher " + (ev.stage0_target || "—")); }
    if ($("learn-verdict")) $("learn-verdict").textContent = (ev.flies && ev.flies[0] && ev.flies[0].weight_drift > 0.01) ? "synapses crawling" : "filing smells";
    set("tagline", "sniffing · ignore the dollar pile on stage0");
    set("ticker", "step " + ev.step + "  " + ev.odor + "  " + ev.executed + "  $" + Number(ev.equity || 0).toFixed(2));
    if ($("frame")) $("frame").src = "/api/frame?t=" + ev.step;
  } catch (err) {
    set("tagline", "state blip: " + (err && err.message ? err.message : "retrying"));
  }
}
tick();
setInterval(tick, 1000);
