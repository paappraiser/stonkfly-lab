const $ = (id) => document.getElementById(id);
function drawCurve(points) {
  const canvas = $("curve"); const ctx = canvas.getContext("2d");
  const w = canvas.width, h = canvas.height; ctx.clearRect(0,0,w,h);
  if (!points || points.length < 2) return;
  const ys = points.map((p) => p[1]); const min = Math.min(...ys); const max = Math.max(...ys);
  const span = Math.max(max - min, 0.01);
  ctx.strokeStyle = "#3ddc97"; ctx.lineWidth = 2; ctx.beginPath();
  points.forEach((p, i) => {
    const x = (i / (points.length - 1)) * (w - 8) + 4;
    const y = h - 8 - ((p[1] - min) / span) * (h - 16);
    if (i === 0) ctx.moveTo(x, y); else ctx.lineTo(x, y);
  });
  ctx.stroke();
}
function flyCard(fly, proposal) {
  const side = proposal ? proposal.side : "HOLD";
  return `<div class="fly"><b>${fly.name}</b><div class="side-${side}">${side} · score ${fly.score.toFixed(3)}</div><div class="sub">sparsity ${(fly.sparsity*100).toFixed(1)}% · drift ${fly.weight_drift.toFixed(3)}</div></div>`;
}
async function tick() {
  try {
    const data = await (await fetch("/api/state", { cache: "no-store" })).json();
    const ev = data.event; if (!ev) return;
    $("title").textContent = `${ev.product}  ${Number(ev.mid).toFixed(2)}`;
    $("world").textContent = data.settings.world;
    $("colony").textContent = `${data.settings.colony} · ${data.settings.n_flies} fly`;
    $("halt").textContent = ev.halted ? ev.halt_reason : "running";
    $("halt").classList.toggle("halt", !!ev.halted);
    $("equity").textContent = `$${Number(ev.equity).toFixed(2)}`;
    $("book").textContent = `cash ${Number(ev.cash).toFixed(2)} · qty ${Number(ev.qty).toFixed(6)} · fee bps ${data.settings.fee_bps}`;
    $("joint").textContent = ev.executed;
    $("joint").className = `big side-${ev.executed}`;
    $("reason").textContent = `${ev.reason} · proposed ${ev.joint.side}`;
    $("odor").textContent = ev.odor;
    $("labels").textContent = ev.labels ? Object.entries(ev.labels).map(([k,v]) => `${k}:${v}`).join("  ") : "";
    const m = ev.metrics || {}; const total = (m.agreements||0)+(m.disagreements||0);
    $("agree").textContent = ev.agreement ? "YES" : "NO";
    $("agree-stats").textContent = `${total ? (100*m.agreements/total).toFixed(0) : "—"}% agree · ${m.fills||0} fills`;
    if (ev.stage0_acc == null) { $("acc").textContent = "n/a"; $("target").textContent = "market world"; }
    else { $("acc").textContent = `${(100*ev.stage0_acc).toFixed(0)}%`; $("target").textContent = `target ${ev.stage0_target||"—"} · n=${m.stage0_decisions}`; }
    $("flies").innerHTML = (ev.flies||[]).map((f,i) => flyCard(f, (ev.proposals||[])[i])).join("");
    drawCurve(data.equity_curve||[]);
    $("frame").src = "/api/frame?t=" + ev.step;
  } catch (err) { $("reason").textContent = "waiting for engine…"; }
}
tick(); setInterval(tick, 1000);
