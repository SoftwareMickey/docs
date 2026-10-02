#!/usr/bin/env node
// features/docs-experience V94 — reproducible, redacted UI screenshots.
//
//   node capture.mjs                    capture every shot in shots.json (Desktop in mock mode; Dashboard against fixtures)
//   node capture.mjs --only desktop     one surface;  --only desktop/machine-overview  one shot
//   node capture.mjs --check            re-capture into a temp dir and fail if any image differs from the manifest (CI/audit)
//   node capture.mjs --redaction-only   run the redaction scan on the live pages without writing images
//   node capture.mjs --dump             print each page's visible text (light theme only) — used to write guides from the shipped UI
//
// No dependencies: Chrome over the DevTools protocol with Node 22's built-in WebSocket and fetch.
// Environment: CHROME (default /usr/bin/google-chrome), DESKTOP_URL (default http://localhost:5199, `pnpm dev:mock` in beaver-desktop/apps/desktop),
//              DASHBOARD_URL (default http://localhost:5173, `npm run dev` in vhb-client; its API is answered from fixtures/dashboard.json).
// Output: ../../images/ui/<surface>/<shot>-<light|dark>.png, ../../images/ui/manifest.json, ../../snippets/screenshots.mdx (capturedAt tag).
import { spawn } from "node:child_process";
import { createHash } from "node:crypto";
import { mkdirSync, writeFileSync, readFileSync, existsSync, mkdtempSync, rmSync } from "node:fs";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { tmpdir } from "node:os";

const HERE = dirname(fileURLToPath(import.meta.url));
const ROOT = resolve(HERE, "../..");
const CHROME = process.env.CHROME || "/usr/bin/google-chrome";
const URLS = { desktop: process.env.DESKTOP_URL || "http://localhost:5199", dashboard: process.env.DASHBOARD_URL || "http://localhost:5173" };
const args = process.argv.slice(2);
const CHECK = args.includes("--check"), REDACTION_ONLY = args.includes("--redaction-only"), DUMP = args.includes("--dump");
const ONLY = args.includes("--only") ? args[args.indexOf("--only") + 1] : null;
const cfg = JSON.parse(readFileSync(join(HERE, "shots.json"), "utf8"));
const FIXTURES = existsSync(join(HERE, "fixtures/dashboard.json")) ? JSON.parse(readFileSync(join(HERE, "fixtures/dashboard.json"), "utf8")) : {};
const FROZEN_NOW = Date.parse(cfg.frozenClock);
const OUT = CHECK ? mkdtempSync(join(tmpdir(), "docs-shots-")) : join(ROOT, "images/ui");

// ---- redaction (Invariant 12): only fictional vocabulary may appear on a captured page -------------------------------------------------
const ALLOWED_EMAIL = /@(beaver\.local|[\w.-]*\.example|example\.(com|org|net)|paperclip\.example)$/i;
const PRIVATE_IP = /^(10\.|127\.|192\.168\.|172\.(1[6-9]|2\d|3[01])\.|169\.254\.|198\.51\.100\.|203\.0\.113\.|192\.0\.2\.|0\.0\.0\.0)/;
const FICTIONAL_HOST = /(^|\.)(local|internal|example|test|invalid|localhost|beaver|paperclip|vectorihub)$/i;
const PUBLIC_DOCS_HOST = /^docs\.vectorihub\.(com|run|dev)$/i;  // the docs site itself — the target of every "Learn more" link, not customer data
export function redactionFindings(text) {
  const bad = [];
  for (const m of text.matchAll(/[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}/g)) if (!ALLOWED_EMAIL.test(m[0])) bad.push(`email ${m[0]}`);
  for (const m of text.matchAll(/\b(\d{1,3})\.(\d{1,3})\.(\d{1,3})\.(\d{1,3})\b/g)) {
    if ([m[1], m[2], m[3], m[4]].some((n) => +n > 255)) continue;
    if (!PRIVATE_IP.test(m[0])) bad.push(`ip ${m[0]}`);
  }
  for (const m of text.matchAll(/\b(?:gh[pousr]_[A-Za-z0-9]{20,}|sk-[A-Za-z0-9_-]{16,}|AKIA[0-9A-Z]{16}|eyJ[A-Za-z0-9_-]{20,}\.[A-Za-z0-9_-]{10,}|xox[abp]-[A-Za-z0-9-]{10,})\b/g)) bad.push(`token ${m[0].slice(0, 8)}…`);
  for (const m of text.matchAll(/\b(?:[a-f0-9]{40,}|[A-Za-z0-9+/]{48,}={0,2})\b/g)) bad.push(`long secret-like string ${m[0].slice(0, 8)}…`);
  for (const m of text.matchAll(/\b((?:[a-z0-9-]+\.)+[a-z]{2,})\b/gi)) {
    const h = m[1].toLowerCase();
    if (/\.(png|svg|jpg|js|ts|css|json|md|txt|yml|yaml|toml|sh|go|py|html|mdx|log|sock|env|conf|ini|lock|mjs|tsx|jsx)$/.test(h)) continue;
    if (/^(e\.g|i\.e|v\d)/.test(h)) continue;
    if (!FICTIONAL_HOST.test(h) && !PUBLIC_DOCS_HOST.test(h) && !/^\d/.test(h)) bad.push(`hostname ${h}`);
  }
  return [...new Set(bad)];
}

// ---- Chrome over CDP ------------------------------------------------------------------------------------------------------------------
class Cdp {
  constructor(ws) { this.ws = ws; this.id = 0; this.pending = new Map(); this.handlers = []; ws.onmessage = (e) => { const m = JSON.parse(e.data); if (m.id && this.pending.has(m.id)) { const { res, rej } = this.pending.get(m.id); this.pending.delete(m.id); m.error ? rej(new Error(m.error.message)) : res(m.result); } else this.handlers.forEach((h) => h(m)); }; }
  send(method, params = {}, sessionId) { const id = ++this.id; this.ws.send(JSON.stringify({ id, method, params, sessionId })); return new Promise((res, rej) => this.pending.set(id, { res, rej })); }
  on(h) { this.handlers.push(h); }
}
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

async function launch() {
  const profile = mkdtempSync(join(tmpdir(), "docs-chrome-"));
  const port = 9300 + Math.floor(Math.random() * 500);
  const proc = spawn(CHROME, ["--headless=new", "--no-sandbox", "--disable-gpu", "--hide-scrollbars", "--force-device-scale-factor=1", "--font-render-hinting=none", `--remote-debugging-port=${port}`, `--user-data-dir=${profile}`, "about:blank"], { stdio: "ignore" });
  let ver; for (let i = 0; i < 50 && !ver; i++) { try { ver = await (await fetch(`http://127.0.0.1:${port}/json/version`)).json(); } catch { await sleep(200); } }
  if (!ver) throw new Error("Chrome did not start");
  const ws = new WebSocket(ver.webSocketDebuggerUrl); await new Promise((r, j) => { ws.onopen = r; ws.onerror = j; });
  return { cdp: new Cdp(ws), proc, profile };
}

async function openPage(cdp, surface, theme) {
  const { targetId } = await cdp.send("Target.createTarget", { url: "about:blank" });
  const { sessionId } = await cdp.send("Target.attachToTarget", { targetId, flatten: true });
  const s = (m, p) => cdp.send(m, p, sessionId);
  await s("Page.enable"); await s("Runtime.enable"); await s("Network.enable");
  if (process.env.DEBUG_CONSOLE) cdp.on((m) => { if (m.sessionId !== sessionId) return; if (m.method === "Runtime.exceptionThrown") console.log("EXC", m.params.exceptionDetails.exception?.description?.slice(0, 400) || m.params.exceptionDetails.text); if (m.method === "Runtime.consoleAPICalled" && ["error", "warning"].includes(m.params.type)) console.log("CON", m.params.type, m.params.args.map((a) => a.value ?? a.description ?? "").join(" ").slice(0, 300)); if (m.method === "Network.loadingFailed") console.log("NETFAIL", m.params.errorText, m.params.requestId); });
  await s("Emulation.setDeviceMetricsOverride", { width: cfg.viewport.width, height: cfg.viewport.height, deviceScaleFactor: 1, mobile: false });
  await s("Emulation.setEmulatedMedia", { features: [{ name: "prefers-color-scheme", value: theme }, { name: "prefers-reduced-motion", value: "reduce" }] });
  // fixed clock + seeded randomness so relative times ("2m ago") and any jitter do not change between runs
  await s("Page.addScriptToEvaluateOnNewDocument", { source: `(() => { const NOW = ${FROZEN_NOW}; const RD = Date; const t0 = RD.now(); const fake = function(...a){ return a.length ? new RD(...a) : new RD(NOW + (RD.now() - t0) * 0); }; fake.prototype = RD.prototype; fake.now = () => NOW; fake.parse = RD.parse; fake.UTC = RD.UTC; globalThis.Date = fake; let seed = 42; Math.random = () => (seed = (seed * 16807) % 2147483647) / 2147483647; try { localStorage.setItem('theme', '${theme}'); localStorage.setItem('beaver.theme', '${theme}'); } catch (e) {} })();` });
  await s("Page.addScriptToEvaluateOnNewDocument", { source: `document.addEventListener('DOMContentLoaded', () => { const st = document.createElement('style'); st.textContent = '*,*::before,*::after{animation:none!important;transition:none!important;caret-color:transparent!important}'; document.head.appendChild(st); });` });
  if (surface === "dashboard") {
    // signed-in session flag the router reads, and a WebSocket that opens and stays silent (the live-update socket has no server here)
    await s("Page.addScriptToEvaluateOnNewDocument", { source: `(() => { try { sessionStorage.setItem('vad', btoa('true')); localStorage.setItem('vhb.activeWorkspace', 'ws_paperclip'); } catch (e) {} class FakeWS extends EventTarget { constructor(u) { super(); this.url = u; this.readyState = 0; this.protocol = ''; setTimeout(() => { this.readyState = 1; const ev = new Event('open'); this.dispatchEvent(ev); this.onopen && this.onopen(ev); }, 10); } send() {} close() { this.readyState = 3; } } FakeWS.CONNECTING = 0; FakeWS.OPEN = 1; FakeWS.CLOSING = 2; FakeWS.CLOSED = 3; window.WebSocket = FakeWS; })();` });
    await s("Fetch.enable", { patterns: [{ urlPattern: "http://localhost:8*/*", requestStage: "Request" }] });
    cdp.on(async (m) => { try {
      if (m.method !== "Fetch.requestPaused" || m.sessionId !== sessionId) return;
      const { requestId, request } = m.params; const path = new URL(request.url).pathname;
      if (process.env.LOG_API) console.log(`API ${request.method} ${path}${new URL(request.url).search}`);
      if (request.method === "OPTIONS") { await s("Fetch.fulfillRequest", { requestId, responseCode: 204, responseHeaders: [{ name: "Access-Control-Allow-Origin", value: request.headers.Origin || "*" }, { name: "Access-Control-Allow-Credentials", value: "true" }, { name: "Access-Control-Allow-Headers", value: request.headers["Access-Control-Request-Headers"] || "content-type" }, { name: "Access-Control-Allow-Methods", value: request.headers["Access-Control-Request-Method"] || "GET" }, { name: "Access-Control-Max-Age", value: "600" }] }); return; }
      const search = new URL(request.url).search; const hit = FIXTURES[`${request.method} ${path}${search}`] ?? FIXTURES[`${request.method} ${path}`] ?? FIXTURES[path];
      const body = hit === undefined ? { status_code: 200, success: true, data: null } : hit;
      await s("Fetch.fulfillRequest", { requestId, responseCode: 200, responseHeaders: [{ name: "Content-Type", value: "application/json" }, { name: "Access-Control-Allow-Origin", value: request.headers.Origin || "*" }, { name: "Access-Control-Allow-Credentials", value: "true" }], body: Buffer.from(JSON.stringify(body)).toString("base64") });
    } catch { /* the page closed while a request was in flight */ } });
  }
  return { s, sessionId, targetId };
}

const evalJs = async (s, expr) => (await s("Runtime.evaluate", { expression: expr, returnByValue: true, awaitPromise: true })).result.value;

async function clickText(s, text, maxY = 1e9) {
  const rect = await evalJs(s, `(() => { const want = ${JSON.stringify(text)}; const maxY = ${maxY}; const vis = (e) => { const r = e.getBoundingClientRect(); const cs = getComputedStyle(e); return r.width > 0 && r.height > 0 && cs.visibility !== 'hidden' && cs.display !== 'none'; };
    const same = (e) => { const t = (e.innerText || '').trim(); return t.split('\\n')[0].trim() === want || t.replace(/\\s+/g, ' ') === want || t.replace(/^[+＋]\\s*/, '') === want; };
    const cands = [...document.querySelectorAll('button,a,[role=button],[role=tab],[role=menuitem],[role=option],li,div,span,td,p')].filter((e) => vis(e) && same(e) && e.getBoundingClientRect().y < maxY);
    if (!cands.length) return null; cands.sort((a, b) => a.getBoundingClientRect().width * a.getBoundingClientRect().height - b.getBoundingClientRect().width * b.getBoundingClientRect().height);
    cands[0].scrollIntoView({ block: 'center' }); const r = cands[0].getBoundingClientRect(); return { x: r.x + r.width / 2, y: r.y + r.height / 2 }; })()`);
  if (!rect) throw new Error(`nothing to click with text "${text}"`);
  await s("Input.dispatchMouseEvent", { type: "mouseMoved", x: rect.x, y: rect.y });
  await s("Input.dispatchMouseEvent", { type: "mousePressed", x: rect.x, y: rect.y, button: "left", clickCount: 1 });
  await s("Input.dispatchMouseEvent", { type: "mouseReleased", x: rect.x, y: rect.y, button: "left", clickCount: 1 });
}

async function runSteps(s, steps) {
  for (const st of steps) {
    if (st.click) await clickText(s, st.click, st.maxY);
    else if (st.focus) await s("Input.dispatchMouseEvent", { type: "mousePressed", x: 700, y: 600, button: "left", clickCount: 1 }).then(() => s("Input.dispatchMouseEvent", { type: "mouseReleased", x: 700, y: 600, button: "left", clickCount: 1 }));
    else if (st.key) { const mod = st.key.startsWith("Control+"); const k = st.key.replace("Control+", ""); await s("Input.dispatchKeyEvent", { type: "keyDown", key: k, code: "Key" + k.toUpperCase(), modifiers: mod ? 2 : 0, windowsVirtualKeyCode: k.toUpperCase().charCodeAt(0) }); await s("Input.dispatchKeyEvent", { type: "keyUp", key: k, code: "Key" + k.toUpperCase(), modifiers: mod ? 2 : 0 }); }
    else if (st.type) await s("Input.insertText", { text: st.type });
    else if (st.goto) { await s("Page.navigate", { url: URLS[st.surface] + st.goto }); }
    await sleep(st.wait ?? 450);
  }
}

async function visibleText(s) {
  return evalJs(s, `(() => { const parts = [document.body.innerText]; document.querySelectorAll('[title],[aria-label],[placeholder],a[href],input,textarea').forEach((e) => { for (const a of ['title','aria-label','placeholder','href','value']) { const v = e.getAttribute?.(a) ?? e[a]; if (v && typeof v === 'string' && !v.startsWith('/') && !v.startsWith('#')) parts.push(v); } }); return parts.join('\\n'); })()`);
}

async function main() {
  const shots = cfg.shots.filter((x) => !ONLY || ONLY === x.surface || ONLY === `${x.surface}/${x.name}`);
  if (!shots.length) { console.error("no shots match", ONLY); process.exit(2); }
  for (const sf of new Set(shots.map((x) => x.surface))) {
    try { const r = await fetch(URLS[sf]); if (!r.ok) throw new Error(r.status); } catch (e) { console.error(`${sf}: ${URLS[sf]} is not reachable (${e.message}) — start it first (see the header of capture.mjs)`); process.exit(2); }
  }
  const { cdp, proc, profile } = await launch();
  const results = [], problems = [];
  try {
    for (const shot of shots) {
      for (const theme of DUMP ? ["light"] : ["light", "dark"]) {
        for (let attempt = 1; attempt <= 3; attempt++) {
          const { s, targetId } = await openPage(cdp, shot.surface, theme);
          try {
            await s("Page.navigate", { url: URLS[shot.surface] + (shot.url || "/") });
            await sleep(shot.settleMs ?? cfg.settleMs); await runSteps(s, shot.steps || []); await sleep(300);
            if (DUMP) { console.log(`\n=== ${shot.surface}/${shot.name}\n` + await evalJs(s, "document.body.innerText")); break; }
            const finds = redactionFindings(await visibleText(s));
            const bodyLen = await evalJs(s, "document.body.innerText.trim().length");
            if (!bodyLen) throw new Error("page rendered no text");
            if (shot.expectText && !(await evalJs(s, `document.body.innerText.toLowerCase().includes(${JSON.stringify(shot.expectText.toLowerCase())})`))) throw new Error(`expected text "${shot.expectText}" not on the page — the click path may have changed`);
            if (finds.length) { problems.push(`${shot.surface}/${shot.name} (${theme}): redaction — ${finds.join(", ")}`); break; }
            if (REDACTION_ONLY) { results.push(`${shot.surface}/${shot.name}-${theme}: clean`); break; }
            const { data } = await s("Page.captureScreenshot", { format: "png", captureBeyondViewport: false });
            const file = `${shot.surface}/${shot.name}-${theme}.png`; const abs = join(OUT, file); mkdirSync(dirname(abs), { recursive: true });
            const buf = Buffer.from(data, "base64"); writeFileSync(abs, buf);
            results.push({ file, surface: shot.surface, name: shot.name, theme, alt: shot.alt, sha256: createHash("sha256").update(buf).digest("hex") });
          } catch (e) {
            problems.push(`${shot.surface}/${shot.name} (${theme}): ${e.message}`);
            if (process.env.DEBUG_DIR) { mkdirSync(process.env.DEBUG_DIR, { recursive: true }); const { data } = await s("Page.captureScreenshot", { format: "png" }); writeFileSync(join(process.env.DEBUG_DIR, `${shot.surface}-${shot.name}-${theme}.png`), Buffer.from(data, "base64")); }
          }
          finally { await cdp.send("Target.closeTarget", { targetId }).catch(() => {}); }
          if (!problems.some((x) => x.startsWith(`${shot.surface}/${shot.name} (${theme})`))) break;
          if (attempt < 3) problems.pop();  // a cold dev server often needs a second load; only the second failure counts
        }
      }
    }
  } finally { proc.kill(); await sleep(1200); rmSync(profile, { recursive: true, force: true, maxRetries: 5, retryDelay: 300 }); }
  if (DUMP) { rmSync(profile, { recursive: true, force: true, maxRetries: 5, retryDelay: 300 }); process.exit(0); }
  if (REDACTION_ONLY) { results.forEach((r) => console.log(r)); }
  else if (CHECK) {
    const man = JSON.parse(readFileSync(join(ROOT, "images/ui/manifest.json"), "utf8")); const by = Object.fromEntries(man.shots.map((x) => [x.file, x.sha256]));
    for (const r of results) if (by[r.file] !== r.sha256) problems.push(`${r.file}: differs from the committed image — the UI changed or the fixtures did; re-run \`node capture.mjs\` and review the diff`);
    rmSync(OUT, { recursive: true, force: true });
  } else if (!ONLY) {
    const capturedAt = new Date().toISOString().slice(0, 10);
    writeFileSync(join(ROOT, "images/ui/manifest.json"), JSON.stringify({ capturedAt, viewport: cfg.viewport, frozenClock: cfg.frozenClock, shots: results }, null, 2) + "\n");
    writeFileSync(join(ROOT, "snippets/screenshots.mdx"), `{/* GENERATED FILE — do not edit. Written by scripts/screenshots/capture.mjs. */}\n\nexport const capturedAt = "${capturedAt}";\n`);
  }
  console.log(`${results.length} image(s) ${REDACTION_ONLY ? "scanned" : CHECK ? "compared" : "written"}, ${problems.length} problem(s)`);
  problems.forEach((p) => console.error("PROBLEM ", p));
  process.exit(problems.length ? 1 : 0);
}
if (import.meta.url === `file://${process.argv[1]}`) main();
