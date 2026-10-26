// Pasek statusu (CLAUDE.md 10.1). Czyta 2 dokumenty przez nasłuch (Z2): meta/status, runner/heartbeat.
import { initializeApp } from "https://www.gstatic.com/firebasejs/10.14.1/firebase-app.js";
import { getFirestore, doc, onSnapshot } from "https://www.gstatic.com/firebasejs/10.14.1/firebase-firestore.js";
import { firebaseConfig } from "./firebase-config.js";

const H = 3600;
const PAIRS = ["EURUSD", "USDJPY", "GBPUSD", "EURGBP", "AUDUSD", "USDCHF", "USDCAD", "EURJPY"];

// Ta sama logika co w apps_script/Code.gs
const lastClosedTs = (now) => Math.floor((now - 60 - H) / H) * H;
function isExpectedBar(ts) {
  const d = new Date(ts * 1000), day = d.getUTCDay(), hr = d.getUTCHours();
  if (day === 6) return false;
  if (day === 5 && hr >= 21) return false;
  if (day === 0 && hr < 22) return false;
  return true;
}
function expectedTs(now) {
  let ts = lastClosedTs(now);
  for (let i = 0; i < 80 && !isExpectedBar(ts); i++) ts -= H;
  return ts;
}

const db = getFirestore(initializeApp(firebaseConfig));
const $ = (id) => document.getElementById(id);
let status = null, beat = null;

function fmtTs(ts) {
  const d = new Date(ts * 1000);
  const utc = d.toISOString().slice(5, 16).replace("T", " ");
  const loc = d.toLocaleString("pl-PL", { hour: "2-digit", minute: "2-digit" });
  return `${utc} UTC · ${loc}`;
}

function setState(dotId, textId, text, color) {
  $(dotId).style.background = `var(--${color})`;
  $(dotId).style.boxShadow = color === "mute" ? "none" : `0 0 10px var(--${color})`;
  $(textId).textContent = text;
}

function sparkline(points) {
  if (!points || points.length < 2) return "";
  const w = 160, h = 28, max = Math.max(...points.map((p) => p.s), 1);
  const xs = points.map((_, i) => (i / (points.length - 1)) * w);
  const d = points.map((p, i) => `${xs[i].toFixed(1)},${(h - (p.s / max) * h).toFixed(1)}`).join(" ");
  return `<svg width="${w}" height="${h}" viewBox="0 0 ${w} ${h}"><polyline fill="none" stroke="var(--accent)" stroke-width="1.5" points="${d}"/></svg>`;
}

function median(a) {
  if (!a.length) return null;
  const s = [...a].sort((x, y) => x - y), m = s.length >> 1;
  return s.length % 2 ? s[m] : (s[m - 1] + s[m]) / 2;
}

function render() {
  const now = Date.now() / 1000;
  const exp = expectedTs(now);
  const closedNow = !isExpectedBar(lastClosedTs(now) + H) && !isExpectedBar(lastClosedTs(now));

  if (!status) {
    setState("dataDot", "dataState", "BRAK DANYCH", "mute");
  } else {
    const pairs = status.pairs || {};
    const lastTs = Math.min(...PAIRS.map((p) => (pairs[p] || {}).lastTs || 0));
    const missingFor = lastTs >= exp ? 0 : now - (exp + H);
    if (missingFor <= 0) setState("dataDot", "dataState", closedNow ? "RYNEK ZAMKNIĘTY" : "DZIAŁA", closedNow ? "mute" : "ok");
    else if (missingFor < 20 * 60) setState("dataDot", "dataState", "DZIAŁA", "ok");
    else if (missingFor < 75 * 60) setState("dataDot", "dataState", "OPÓŹNIENIE", "warn");
    else setState("dataDot", "dataState", "STOI", "bad");

    const lat = status.latency24h || [];
    const last = lat.length ? lat[lat.length - 1].s : null;
    const med = median(lat.map((x) => x.s));
    $("latency").textContent = last === null ? "— s" : `${last} s`;
    $("latencySub").innerHTML = (med === null ? "" : `mediana 24 h: ${Math.round(med)} s`) + sparkline(lat);
    $("bars").textContent = (status.totalBars || 0).toLocaleString("pl-PL");

    const flagsCount = PAIRS.reduce((s, p) => s + ((pairs[p] || {}).flags || []).length, 0)
      + ((status.cross || {}).flags || []).length;
    $("flags").textContent = flagsCount;
    if (status.lastRun && !status.lastRun.ok) $("flagsSub").textContent = `Błąd: ${status.lastRun.error}`;

    $("pairsBody").innerHTML = PAIRS.map((p) => {
      const s = pairs[p] || {};
      const fl = (s.flags || []).length;
      return `<tr><td>${p}</td><td>${s.lastTs ? fmtTs(s.lastTs) : "—"}</td>
        <td class="num">${s.latencySec ?? "—"}</td><td class="num">${(s.count || 0).toLocaleString("pl-PL")}</td>
        <td class="num" title="${(s.flags || []).join("\n")}">${fl ? "⚠ " + fl : "0"}</td></tr>`;
    }).join("");
  }

  const seen = beat && beat.lastSeen ? (beat.lastSeen.seconds ?? beat.lastSeen) : 0;
  if (seen && now - seen < 90 && beat.state !== "offline") {
    const job = beat.job && beat.job.id ? ` · ${beat.job.progress ?? 0}%` : "";
    setState("macDot", "macState", "POŁĄCZONY" + job, "ok");
  } else {
    setState("macDot", "macState", "ROZŁĄCZONY", "mute");
  }
}

onSnapshot(doc(db, "meta", "status"), (s) => { status = s.data() || null; render(); },
  (e) => { $("flagsSub").textContent = "Firestore: " + e.code; });
onSnapshot(doc(db, "runner", "heartbeat"), (s) => { beat = s.data() || null; render(); }, () => {});
setInterval(render, 15000);
render();
