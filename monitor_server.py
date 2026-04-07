"""
Ximen Nao Agent Hub — Monitoring Server
Minimal, artistic dashboard for visualizing agent system activity.
Run: python monitor_server.py
Visit: http://localhost:7777
"""

import json
import os
from pathlib import Path
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse

DATA_DIR = Path(__file__).parent / "data"

AGENTS = {
    "Big Head": {
        "key": "kk",
        "animal": "Human",
        "glyph": "人",
        "color": "#b07fd4",
        "desc": "Meta-agent. Sees everything. Routes nothing — simply knows.",
        "outputs": ["System health reports", "Agent reviews", "Strategic reflection"],
    },
    "Donkey": {
        "key": "intelligence",
        "animal": "Donkey",
        "glyph": "驴",
        "color": "#d4a84b",
        "desc": "First life. Alert ears, unstoppable gallop. AI news from every source.",
        "outputs": ["Daily AI digest", "Top stories by theme", "Hot takes on hype"],
    },
    "Ox": {
        "key": "todo",
        "animal": "Ox",
        "glyph": "牛",
        "color": "#6aab7a",
        "desc": "Second life. Steady and tireless. Plows through your task list.",
        "outputs": ["Task creation", "Task completion", "Prioritized todo list"],
    },
    "Pig": {
        "key": "research",
        "animal": "Pig",
        "glyph": "猪",
        "color": "#d47a5a",
        "desc": "Third life. Cunning beneath the mud. Market intelligence, business clarity.",
        "outputs": ["Market analysis", "Competitor mapping", "Opportunity scoring"],
    },
    "Dog": {
        "key": "health",
        "animal": "Dog",
        "glyph": "犬",
        "color": "#5a8fd4",
        "desc": "Fourth life. Loyal guardian. Healthcare research for the family.",
        "outputs": ["Evidence-based health guidance", "Drug interactions", "US product recommendations"],
    },
}

HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Ximen Nao · Agent Hub</title>
<style>
  @import url('https://fonts.googleapis.com/css2?family=EB+Garamond:ital,wght@0,400;0,500;1,400&family=Noto+Serif+SC:wght@300;400&display=swap');

  *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

  :root {
    --bg: #080808;
    --surface: #111111;
    --border: #1e1e1e;
    --muted: #444;
    --text: #c8c0b0;
    --text-dim: #5a5550;
    --ink: #e8e0d0;
  }

  html, body {
    background: var(--bg);
    color: var(--text);
    font-family: 'EB Garamond', Georgia, serif;
    font-size: 18px;
    line-height: 1.75;
    min-height: 100vh;
  }

  /* subtle ink wash background */
  body::before {
    content: '';
    position: fixed;
    inset: 0;
    background: radial-gradient(ellipse 80% 60% at 50% 0%, #1a1208 0%, transparent 70%),
                radial-gradient(ellipse 60% 80% at 80% 100%, #080e1a 0%, transparent 70%);
    pointer-events: none;
    z-index: 0;
  }

  .layout {
    position: relative;
    z-index: 1;
    display: grid;
    grid-template-columns: 1fr 340px;
    grid-template-rows: auto 1fr;
    grid-template-areas:
      "header header"
      "main   feed";
    min-height: 100vh;
    max-width: 1400px;
    margin: 0 auto;
    gap: 0;
  }

  /* ── HEADER ── */
  header {
    grid-area: header;
    padding: 48px 48px 32px;
    border-bottom: 1px solid var(--border);
    display: flex;
    align-items: flex-end;
    justify-content: space-between;
    gap: 24px;
  }

  .site-title {
    font-family: 'Noto Serif SC', serif;
    font-size: 13px;
    font-weight: 300;
    letter-spacing: 0.25em;
    color: var(--text-dim);
    text-transform: uppercase;
  }

  .site-name {
    font-size: 2.4rem;
    font-weight: 400;
    color: var(--ink);
    letter-spacing: 0.02em;
    line-height: 1.1;
    margin-top: 6px;
  }

  .site-name em {
    font-style: italic;
    color: var(--text-dim);
    font-size: 1.2rem;
    display: block;
    margin-top: 4px;
  }

  .pulse-ring {
    width: 10px; height: 10px;
    border-radius: 50%;
    background: #4aaa6a;
    box-shadow: 0 0 0 0 rgba(74,170,106,.4);
    animation: pulse 2.5s ease infinite;
    display: inline-block;
    margin-right: 8px;
  }
  @keyframes pulse {
    0%   { box-shadow: 0 0 0 0 rgba(74,170,106,.4); }
    70%  { box-shadow: 0 0 0 8px rgba(74,170,106,0); }
    100% { box-shadow: 0 0 0 0 rgba(74,170,106,0); }
  }

  .header-meta {
    text-align: right;
    font-size: 13px;
    color: var(--text-dim);
    font-family: 'Noto Serif SC', serif;
    font-weight: 300;
  }

  .header-meta .live { color: #4aaa6a; }

  /* ── MAIN ── */
  main {
    grid-area: main;
    padding: 40px 48px 48px;
    overflow-y: auto;
  }

  /* ── CONSTELLATION ── */
  .constellation {
    position: relative;
    height: 260px;
    margin-bottom: 56px;
  }

  .constellation svg {
    position: absolute;
    inset: 0;
    width: 100%;
    height: 100%;
  }

  /* ── AGENT GRID ── */
  .section-label {
    font-family: 'Noto Serif SC', serif;
    font-size: 11px;
    font-weight: 300;
    letter-spacing: 0.35em;
    color: var(--text-dim);
    text-transform: uppercase;
    margin-bottom: 20px;
  }

  .agents {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
    gap: 1px;
    background: var(--border);
    border: 1px solid var(--border);
    margin-bottom: 48px;
  }

  .agent-card {
    background: var(--surface);
    padding: 24px;
    position: relative;
    overflow: hidden;
    transition: background .2s;
  }

  .agent-card:hover { background: #161616; }

  .agent-card::before {
    content: attr(data-glyph);
    position: absolute;
    right: 12px;
    bottom: -12px;
    font-family: 'Noto Serif SC', serif;
    font-size: 96px;
    color: var(--agent-color);
    opacity: .04;
    line-height: 1;
    pointer-events: none;
    transition: opacity .3s;
  }
  .agent-card:hover::before { opacity: .07; }

  /* ── Agent Art Banner ── */
  .agent-art {
    margin: -24px -24px 20px -24px;
    height: 96px;
    position: relative;
    overflow: hidden;
    display: flex;
    align-items: center;
    justify-content: center;
    background: linear-gradient(160deg, color-mix(in srgb, var(--agent-color) 12%, transparent), color-mix(in srgb, var(--agent-color) 4%, #0a0a0a));
    border-bottom: 1px solid color-mix(in srgb, var(--agent-color) 20%, transparent);
  }

  .agent-art-glyph {
    font-family: 'Noto Serif SC', serif;
    font-size: 58px;
    color: var(--agent-color);
    opacity: 0.75;
    line-height: 1;
    text-shadow: 0 0 32px color-mix(in srgb, var(--agent-color) 60%, transparent),
                 0 0 80px color-mix(in srgb, var(--agent-color) 25%, transparent);
    transition: opacity .3s, text-shadow .3s;
  }
  .agent-card:hover .agent-art-glyph {
    opacity: 0.95;
    text-shadow: 0 0 24px color-mix(in srgb, var(--agent-color) 80%, transparent),
                 0 0 64px color-mix(in srgb, var(--agent-color) 40%, transparent);
  }

  .agent-art-line {
    position: absolute;
    bottom: 0;
    left: 24px;
    right: 24px;
    height: 1px;
    background: linear-gradient(90deg, transparent, var(--agent-color), transparent);
    opacity: 0.18;
  }

  .agent-art-dots {
    position: absolute;
    top: 12px;
    right: 16px;
    display: flex;
    gap: 4px;
  }
  .agent-art-dots span {
    width: 4px;
    height: 4px;
    border-radius: 50%;
    background: var(--agent-color);
    opacity: 0.2;
  }

  .agent-name {
    font-size: 1.2rem;
    font-weight: 500;
    color: var(--ink);
    margin-bottom: 2px;
  }

  .agent-animal {
    font-family: 'Noto Serif SC', serif;
    font-size: 12px;
    letter-spacing: 0.2em;
    color: var(--agent-color);
    text-transform: uppercase;
    margin-bottom: 12px;
  }

  .agent-desc {
    font-size: 15px;
    color: var(--text-dim);
    font-style: italic;
    line-height: 1.6;
    margin-bottom: 16px;
  }

  .agent-outputs {
    list-style: none;
    padding: 0;
    border-top: 1px solid var(--border);
    padding-top: 14px;
  }

  .agent-outputs li {
    font-size: 13.5px;
    color: var(--text-dim);
    padding: 3px 0;
    padding-left: 16px;
    position: relative;
  }

  .agent-outputs li::before {
    content: '→';
    position: absolute;
    left: 0;
    color: var(--agent-color);
    opacity: .5;
  }

  .last-active {
    font-size: 11px;
    color: var(--text-dim);
    margin-top: 14px;
    font-family: monospace;
  }

  .last-active span {
    color: var(--agent-color);
    opacity: .8;
  }

  /* ── TODO STRIP ── */
  .todo-section {
    border-top: 1px solid var(--border);
    padding-top: 36px;
  }

  .todo-list {
    display: flex;
    flex-direction: column;
    gap: 0;
  }

  .todo-item {
    display: flex;
    align-items: center;
    gap: 14px;
    padding: 12px 0;
    border-bottom: 1px solid var(--border);
    font-size: 15.5px;
  }

  .todo-check {
    width: 14px; height: 14px;
    border: 1px solid var(--muted);
    border-radius: 2px;
    flex-shrink: 0;
    position: relative;
  }

  .todo-check.done {
    background: #2a3d2e;
    border-color: #4aaa6a44;
  }

  .todo-check.done::after {
    content: '✓';
    position: absolute;
    inset: 0;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 9px;
    color: #4aaa6a;
  }

  .todo-text {
    color: var(--text);
    flex: 1;
  }

  .todo-text.done { color: var(--text-dim); text-decoration: line-through; }

  .empty-state {
    color: var(--text-dim);
    font-style: italic;
    font-size: 14px;
    padding: 16px 0;
  }

  /* ── FEED SIDEBAR ── */
  aside {
    grid-area: feed;
    border-left: 1px solid var(--border);
    display: flex;
    flex-direction: column;
    overflow: hidden;
  }

  .feed-header {
    padding: 40px 24px 16px;
    border-bottom: 1px solid var(--border);
    font-family: 'Noto Serif SC', serif;
    font-size: 11px;
    letter-spacing: 0.35em;
    color: var(--text-dim);
    text-transform: uppercase;
    flex-shrink: 0;
  }

  .feed-list {
    flex: 1;
    overflow-y: auto;
    padding: 0;
  }

  .feed-list::-webkit-scrollbar { width: 2px; }
  .feed-list::-webkit-scrollbar-thumb { background: var(--border); }

  .feed-item {
    padding: 20px 24px;
    border-bottom: 1px solid var(--border);
    animation: fadeIn .4s ease;
  }

  @keyframes fadeIn {
    from { opacity: 0; transform: translateY(-4px); }
    to   { opacity: 1; transform: translateY(0); }
  }

  .feed-agent {
    font-size: 11px;
    letter-spacing: 0.15em;
    text-transform: uppercase;
    margin-bottom: 6px;
  }

  .feed-time {
    font-size: 10px;
    color: var(--text-dim);
    font-family: monospace;
    margin-bottom: 8px;
  }

  .feed-query {
    font-size: 14px;
    color: var(--text-dim);
    font-style: italic;
    margin-bottom: 8px;
    line-height: 1.55;
  }

  .feed-preview {
    font-size: 13.5px;
    color: var(--text);
    line-height: 1.6;
    opacity: .75;
    display: -webkit-box;
    -webkit-line-clamp: 4;
    -webkit-box-orient: vertical;
    overflow: hidden;
  }

  .feed-length {
    font-size: 11px;
    color: var(--text-dim);
    font-family: monospace;
    margin-top: 8px;
  }

  .feed-empty {
    padding: 32px 24px;
    color: var(--text-dim);
    font-style: italic;
    font-size: 14px;
    line-height: 1.6;
  }

  /* scrollbar for main */
  main::-webkit-scrollbar { width: 2px; }
  main::-webkit-scrollbar-thumb { background: var(--border); }

  @media (max-width: 900px) {
    .layout {
      grid-template-columns: 1fr;
      grid-template-areas: "header" "main" "feed";
    }
    aside { border-left: none; border-top: 1px solid var(--border); max-height: 400px; }
    header { padding: 32px 24px 24px; }
    main { padding: 28px 24px 40px; }
  }
</style>
</head>
<body>

<div class="layout">

  <header>
    <div>
      <div class="site-title">Ximen Nao · 西门闹</div>
      <div class="site-name">
        Agent Hub
        <em>Life and Death Are Wearing Me Out</em>
      </div>
    </div>
    <div class="header-meta">
      <div><span class="pulse-ring"></span><span class="live">live</span></div>
      <div id="last-updated" style="margin-top:6px">—</div>
      <div id="log-count" style="margin-top:4px">loading…</div>
    </div>
  </header>

  <main>

    <!-- Constellation diagram -->
    <div class="section-label">System Architecture</div>
    <div class="constellation" id="constellation-wrap">
      <svg id="constellation" viewBox="0 0 800 220" preserveAspectRatio="xMidYMid meet">
        <!-- Lines from supervisor to agents (drawn by JS) -->
        <g id="lines"></g>
        <!-- Nodes drawn by JS -->
        <g id="nodes"></g>
      </svg>
    </div>

    <!-- Agent Cards -->
    <div class="section-label">The Reincarnations</div>
    <div class="agents" id="agent-cards"></div>

    <!-- Todo -->
    <div class="todo-section">
      <div class="section-label" style="margin-bottom:16px">Ox's Plow — Current Tasks</div>
      <div class="todo-list" id="todo-list"><div class="empty-state">Loading tasks…</div></div>
    </div>

  </main>

  <aside>
    <div class="feed-header">Activity Stream</div>
    <div class="feed-list" id="feed-list">
      <div class="feed-empty">Waiting for the agents to speak…</div>
    </div>
  </aside>

</div>

<script>
const AGENTS_META = __AGENTS_JSON__;

// Build a reverse lookup: agent key → metadata
const agentByKey = {};
Object.entries(AGENTS_META).forEach(([name, a]) => { agentByKey[a.key] = { ...a, displayName: name }; });

// Resolve either display name OR agent key to metadata
const resolveAgent = name => AGENTS_META[name] || agentByKey[name] || {};
const agentColor   = name => resolveAgent(name).color || '#888';
const agentGlyph   = name => resolveAgent(name).glyph || '?';
const agentDisplay = name => {
  if (AGENTS_META[name]) return name;
  return (agentByKey[name] || {}).displayName || name;
};

// ── Agent Cards ────────────────────────────────────────────────────────────
function renderCards(logs) {
  const lastActive = {};
  logs.forEach(l => { lastActive[l.agent] = l.timestamp; });

  const container = document.getElementById('agent-cards');
  container.innerHTML = Object.entries(AGENTS_META).map(([name, a]) => {
    const ts = lastActive[name] || lastActive[a.key];
    const timeStr = ts ? ts.slice(0,16).replace('T',' ') : 'never';
    return `<div class="agent-card" data-glyph="${a.glyph}"
              style="--agent-color:${a.color}">
      <div class="agent-art">
        <div class="agent-art-glyph">${a.glyph}</div>
        <div class="agent-art-line"></div>
        <div class="agent-art-dots"><span></span><span></span><span></span></div>
      </div>
      <div class="agent-name">${name}</div>
      <div class="agent-animal">${a.animal}</div>
      <div class="agent-desc">${a.desc}</div>
      <ul class="agent-outputs">
        ${a.outputs.map(o => `<li>${o}</li>`).join('')}
      </ul>
      <div class="last-active">last active <span>${timeStr}</span></div>
    </div>`;
  }).join('');
}

// ── Constellation ──────────────────────────────────────────────────────────
function renderConstellation() {
  const svg = document.getElementById('constellation');
  const linesG = document.getElementById('lines');
  const nodesG = document.getElementById('nodes');
  linesG.innerHTML = ''; nodesG.innerHTML = '';

  const W = 800, H = 220;
  const cx = W/2, cy = H/2;

  // Supervisor in center
  const supervisor = {x: cx, y: cy, label: 'Supervisor', sub: 'Router'};

  // Agents in arc
  const names = Object.keys(AGENTS_META);
  const count = names.length;
  const radius = 90;
  const startAngle = -Math.PI * 0.9;
  const endAngle   =  Math.PI * 0.9;

  const positions = names.map((name, i) => {
    const t = count === 1 ? 0.5 : i / (count - 1);
    const angle = startAngle + t * (endAngle - startAngle);
    return {
      x: cx + radius * 1.9 * Math.cos(angle),
      y: cy + radius * 0.85 * Math.sin(angle),
      name,
      color: AGENTS_META[name].color,
      glyph: AGENTS_META[name].glyph,
    };
  });

  // Draw lines
  positions.forEach(p => {
    const el = document.createElementNS('http://www.w3.org/2000/svg','line');
    el.setAttribute('x1', supervisor.x);
    el.setAttribute('y1', supervisor.y);
    el.setAttribute('x2', p.x);
    el.setAttribute('y2', p.y);
    el.setAttribute('stroke', p.color);
    el.setAttribute('stroke-width', '0.6');
    el.setAttribute('opacity', '0.18');
    linesG.appendChild(el);
  });

  // Draw supervisor node
  const sg = document.createElementNS('http://www.w3.org/2000/svg','g');
  const sc = document.createElementNS('http://www.w3.org/2000/svg','circle');
  sc.setAttribute('cx', supervisor.x); sc.setAttribute('cy', supervisor.y);
  sc.setAttribute('r', '16'); sc.setAttribute('fill', '#1a1a1a');
  sc.setAttribute('stroke', '#333'); sc.setAttribute('stroke-width', '1');
  const st = document.createElementNS('http://www.w3.org/2000/svg','text');
  st.setAttribute('x', supervisor.x); st.setAttribute('y', supervisor.y + 5);
  st.setAttribute('text-anchor','middle'); st.setAttribute('fill','#777');
  st.setAttribute('font-size','10'); st.setAttribute('font-family','Noto Serif SC, serif');
  st.textContent = '路';
  const sl = document.createElementNS('http://www.w3.org/2000/svg','text');
  sl.setAttribute('x', supervisor.x); sl.setAttribute('y', supervisor.y + 30);
  sl.setAttribute('text-anchor','middle'); sl.setAttribute('fill','#444');
  sl.setAttribute('font-size','9'); sl.setAttribute('font-family','EB Garamond, serif');
  sl.setAttribute('letter-spacing','1');
  sl.textContent = 'SUPERVISOR';
  sg.appendChild(sc); sg.appendChild(st); sg.appendChild(sl);
  nodesG.appendChild(sg);

  // Draw agent nodes
  positions.forEach(p => {
    const g = document.createElementNS('http://www.w3.org/2000/svg','g');
    const c = document.createElementNS('http://www.w3.org/2000/svg','circle');
    c.setAttribute('cx', p.x); c.setAttribute('cy', p.y);
    c.setAttribute('r', '20'); c.setAttribute('fill', '#111');
    c.setAttribute('stroke', p.color); c.setAttribute('stroke-width', '0.8');
    c.setAttribute('opacity', '0.9');
    const gt = document.createElementNS('http://www.w3.org/2000/svg','text');
    gt.setAttribute('x', p.x); gt.setAttribute('y', p.y + 6);
    gt.setAttribute('text-anchor','middle'); gt.setAttribute('fill', p.color);
    gt.setAttribute('font-size','15'); gt.setAttribute('font-family','Noto Serif SC, serif');
    gt.setAttribute('opacity','0.7');
    gt.textContent = p.glyph;
    const lt = document.createElementNS('http://www.w3.org/2000/svg','text');
    const below = p.y > cy;
    lt.setAttribute('x', p.x);
    lt.setAttribute('y', below ? p.y + 36 : p.y - 26);
    lt.setAttribute('text-anchor','middle'); lt.setAttribute('fill','#555');
    lt.setAttribute('font-size','9'); lt.setAttribute('font-family','EB Garamond, serif');
    lt.setAttribute('letter-spacing','1');
    lt.textContent = p.name.toUpperCase();
    g.appendChild(c); g.appendChild(gt); g.appendChild(lt);
    nodesG.appendChild(g);
  });
}

// ── Feed ────────────────────────────────────────────────────────────────────
function renderFeed(logs) {
  const container = document.getElementById('feed-list');
  if (!logs.length) {
    container.innerHTML = '<div class="feed-empty">No activity recorded yet.</div>';
    return;
  }
  const reversed = [...logs].reverse();
  container.innerHTML = reversed.map(l => {
    const color = agentColor(l.agent);
    const name  = agentDisplay(l.agent);
    return `<div class="feed-item">
      <div class="feed-agent" style="color:${color}">${name}</div>
      <div class="feed-time">${l.timestamp.slice(0,16).replace('T',' ')}</div>
      <div class="feed-query">"${l.query}"</div>
      <div class="feed-preview">${l.response_preview}</div>
      <div class="feed-length">${l.response_length} chars</div>
    </div>`;
  }).join('');
}

// ── Todos ───────────────────────────────────────────────────────────────────
function renderTodos(todos) {
  const container = document.getElementById('todo-list');
  if (!todos.length) {
    container.innerHTML = '<div class="empty-state">No tasks yet — Ox rests.</div>';
    return;
  }
  container.innerHTML = todos.map(t => `
    <div class="todo-item">
      <div class="todo-check ${t.done ? 'done' : ''}"></div>
      <div class="todo-text ${t.done ? 'done' : ''}">${t.task}</div>
    </div>`).join('');
}

// ── Poll ────────────────────────────────────────────────────────────────────
async function refresh() {
  try {
    const [logsRes, todosRes] = await Promise.all([
      fetch('/api/logs'),
      fetch('/api/todos'),
    ]);
    const logs  = await logsRes.json();
    const todos = await todosRes.json();

    renderCards(logs);
    renderFeed(logs);
    renderTodos(todos);

    document.getElementById('last-updated').textContent =
      new Date().toLocaleTimeString();
    document.getElementById('log-count').textContent =
      `${logs.length} events logged`;
  } catch(e) {
    document.getElementById('last-updated').textContent = 'error';
  }
}

renderConstellation();
refresh();
setInterval(refresh, 6000);
</script>
</body>
</html>
"""


class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        pass  # silence default logging

    def _json(self, data):
        body = json.dumps(data, ensure_ascii=False).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", len(body))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def _html(self, body: str):
        encoded = body.encode()
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", len(encoded))
        self.end_headers()
        self.wfile.write(encoded)

    def do_GET(self):
        path = urlparse(self.path).path

        if path == "/api/logs":
            fp = DATA_DIR / "agent_logs.json"
            data = json.loads(fp.read_text()) if fp.exists() else []
            self._json(data)

        elif path == "/api/todos":
            fp = DATA_DIR / "todos.json"
            data = json.loads(fp.read_text()) if fp.exists() else []
            self._json(data)

        elif path == "/api/agents":
            self._json(AGENTS)

        elif path in ("/", "/index.html"):
            # Inject agents metadata into the HTML template
            agents_json = json.dumps(AGENTS, ensure_ascii=False)
            page = HTML.replace("__AGENTS_JSON__", agents_json)
            self._html(page)

        else:
            self.send_response(404)
            self.end_headers()


if __name__ == "__main__":
    port = int(os.environ.get("MONITOR_PORT", 7777))
    server = HTTPServer(("0.0.0.0", port), Handler)
    print(f"\n  Ximen Nao · Agent Hub Monitor")
    print(f"  ─────────────────────────────")
    print(f"  http://localhost:{port}\n")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n  Shutting down.\n")
