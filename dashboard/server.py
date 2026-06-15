"""JARVIS Web Dashboard — localhost:8765.

Tek dosya FastAPI + dahili HTML. JARVIS arka planda başlatır.

Endpoints:
  GET  /                  → SPA (HTML + JS, tek dosya)
  GET  /api/stats         → toplam tool sayısı, son komutlar, başarı oranı
  GET  /api/log?n=50      → son N olay
  GET  /api/tools         → mevcut tool isimleri
  POST /api/memory        → manuel `remember`
  GET  /api/health        → uptime + RAM
"""
from __future__ import annotations

import sqlite3
import time
from pathlib import Path
from typing import Any

import asyncio

import psutil
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse

_DB = Path.home() / ".jarvis" / "memory" / "episodic.db"
_STARTED = time.time()

app = FastAPI(title="JARVIS Dashboard", docs_url=None, redoc_url=None)


def _db():
    if not _DB.exists():
        return None
    conn = sqlite3.connect(str(_DB), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


@app.get("/api/health")
def health():
    proc = psutil.Process()
    return {
        "uptime_s": int(time.time() - _STARTED),
        "rss_mb": round(proc.memory_info().rss / 1024 / 1024, 1),
        "cpu_percent": round(proc.cpu_percent(interval=None), 1),
        "threads": proc.num_threads(),
    }


@app.get("/api/stats")
def stats():
    conn = _db()
    if conn is None:
        return {"empty": True}
    try:
        total = conn.execute("SELECT COUNT(*) FROM events").fetchone()[0]
        today = conn.execute(
            "SELECT COUNT(*) FROM events WHERE day = date('now')"
        ).fetchone()[0]
        success = conn.execute(
            "SELECT COUNT(*) FROM events WHERE category='command' AND ok=1"
        ).fetchone()[0]
        fails = conn.execute(
            "SELECT COUNT(*) FROM events WHERE category='command_error' OR ok=0"
        ).fetchone()[0]
        top_tools = [
            {"tool": r["tool"], "n": r["c"]}
            for r in conn.execute(
                "SELECT tool, COUNT(*) c FROM events "
                "WHERE tool IS NOT NULL AND ok=1 "
                "GROUP BY tool ORDER BY c DESC LIMIT 10"
            ).fetchall()
        ]
        return {
            "total": total, "today": today,
            "success": success, "fails": fails,
            "success_rate": round(success * 100 / max(success + fails, 1), 1),
            "top_tools": top_tools,
        }
    finally:
        conn.close()


@app.get("/api/log")
def get_log(n: int = 50):
    conn = _db()
    if conn is None:
        return []
    try:
        n = max(1, min(n, 500))
        rows = conn.execute(
            "SELECT ts, category, summary, ok FROM events ORDER BY id DESC LIMIT ?", (n,)
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


@app.get("/api/telemetry")
def telemetry(days: int = 7):
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    try:
        from memory.episodic import get_tool_telemetry
        return get_tool_telemetry(days=days)
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


@app.get("/api/transcript")
def transcript(n: int = 30):
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    try:
        from memory.transcripts import get_recent_turns
        return get_recent_turns(n=min(n, 200))
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


@app.get("/api/tools")
def list_tools():
    actions = Path(__file__).resolve().parent.parent / "actions"
    import ast as _ast
    tools = []
    for f in sorted(actions.glob("*.py")):
        if f.name.startswith("_"):
            continue
        try:
            tree = _ast.parse(f.read_text(encoding="utf-8"))
            for node in tree.body:
                if isinstance(node, _ast.FunctionDef) and node.name.endswith("_action") and not node.name.startswith("_"):
                    tools.append({"name": node.name[:-len("_action")], "file": f.name})
        except Exception:
            continue
    return tools


@app.post("/api/memory")
def memory_remember(payload: dict[str, Any]):
    text = (payload.get("text") or "").strip()
    if not text:
        raise HTTPException(400, "text gerekli")
    try:
        import sys
        sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
        from memory.vector_memory import remember
        rid = remember(text, kind=payload.get("kind", "manual"))
        return {"id": rid}
    except Exception as e:
        raise HTTPException(500, str(e))


_INDEX_HTML = """<!doctype html>
<html lang="tr">
<head>
<meta charset="utf-8">
<title>JARVIS · Dashboard</title>
<style>
  :root { --bg:#0a0e14; --fg:#c9d1d9; --muted:#586069; --accent:#00bfff; --ok:#3fb950; --fail:#f85149; --card:#0d1117; }
  *{box-sizing:border-box;margin:0;padding:0;font-family:system-ui,-apple-system,Segoe UI,Roboto,sans-serif}
  body{background:var(--bg);color:var(--fg);padding:24px;font-size:14px}
  h1{font-weight:300;letter-spacing:.04em;margin-bottom:24px;color:var(--accent);font-size:24px}
  .grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:16px;margin-bottom:24px}
  .card{background:var(--card);border:1px solid #1f2937;border-radius:8px;padding:16px}
  .card h2{font-size:12px;color:var(--muted);text-transform:uppercase;letter-spacing:.08em;margin-bottom:8px}
  .num{font-size:28px;font-weight:200;color:var(--accent)}
  .row{display:flex;justify-content:space-between;padding:4px 0;border-bottom:1px solid #1f2937;font-size:13px}
  .row:last-child{border:0}
  .ok{color:var(--ok)} .fail{color:var(--fail)} .muted{color:var(--muted)}
  pre{font-family:Consolas,Monaco,monospace;font-size:12px;white-space:pre-wrap;line-height:1.5}
  .log-entry{padding:6px 0;border-bottom:1px solid #1f2937;font-size:12px}
  .log-entry .ts{color:var(--muted);margin-right:8px}
  .tag{display:inline-block;padding:1px 6px;border-radius:3px;background:#1f2937;font-size:10px;margin-right:6px}
  input,button{background:#1f2937;color:var(--fg);border:0;padding:8px 12px;border-radius:4px;font-size:13px}
  button{background:var(--accent);color:#000;cursor:pointer;font-weight:600}
  button:hover{opacity:.9}
</style>
</head>
<body>
<h1>⚡ JARVIS · Dashboard</h1>
<div class="grid" id="cards"></div>
<div class="card">
  <h2>Bellek ekle</h2>
  <div style="display:flex;gap:8px;margin-top:8px">
    <input id="memText" placeholder="JARVIS'in hatırlamasını istediğin şey..." style="flex:1">
    <button onclick="remember()">Kaydet</button>
  </div>
  <div id="memMsg" class="muted" style="margin-top:6px;font-size:12px"></div>
</div>
<div class="card" style="margin-top:16px">
  <h2>Tool Telemetri (7 gün) — ortalama gecikme & başarı</h2>
  <div id="telemetry"></div>
</div>
<div class="card" style="margin-top:16px">
  <h2>Son Olaylar</h2>
  <div id="log"></div>
</div>

<script>
async function load(){
  const [h,s,l,tel] = await Promise.all([
    fetch('/api/health').then(r=>r.json()),
    fetch('/api/stats').then(r=>r.json()),
    fetch('/api/log?n=30').then(r=>r.json()),
    fetch('/api/telemetry').then(r=>r.json()).catch(()=>[]),
  ]);
  const telDiv = document.getElementById('telemetry');
  if(telDiv){
    telDiv.innerHTML = (Array.isArray(tel)&&tel.length) ? tel.map(t=>{
      const ms = t.avg_ms!=null ? t.avg_ms+'ms' : '—';
      const sr = t.success_rate;
      const col = sr>=90?'ok':(sr>=60?'':'fail');
      return `<div class="row"><span>${t.tool}</span><span><span class="muted">${t.calls}× · ${ms} · </span><span class="${col}">${sr}%</span></span></div>`;
    }).join('') : '<span class="muted">henüz veri yok</span>';
  }
  document.getElementById('cards').innerHTML = `
    <div class="card"><h2>Toplam Olay</h2><div class="num">${s.total||0}</div></div>
    <div class="card"><h2>Bugün</h2><div class="num">${s.today||0}</div></div>
    <div class="card"><h2>Başarı Oranı</h2><div class="num">${(s.success_rate||0)}%</div><div class="muted" style="font-size:11px">${s.success||0} OK / ${s.fails||0} FAIL</div></div>
    <div class="card"><h2>RAM</h2><div class="num">${h.rss_mb||0} MB</div><div class="muted" style="font-size:11px">${h.threads||0} thread · ${Math.floor((h.uptime_s||0)/60)}dk uptime</div></div>
    <div class="card"><h2>En Sık Tool'lar</h2>${(s.top_tools||[]).map(t=>`<div class="row"><span>${t.tool}</span><span class="muted">${t.n}</span></div>`).join('')||'<span class="muted">veri yok</span>'}</div>
  `;
  document.getElementById('log').innerHTML = (l||[]).map(e=>{
    const cls = e.ok===0 ? 'fail' : (e.category==='command'?'ok':'');
    return `<div class="log-entry"><span class="ts">${e.ts.split('T')[1]}</span><span class="tag">${e.category}</span><span class="${cls}">${e.summary}</span></div>`;
  }).join('') || '<span class="muted">henüz olay yok</span>';
}
async function remember(){
  const text = document.getElementById('memText').value.trim();
  if(!text){return}
  const r = await fetch('/api/memory',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({text})});
  const data = await r.json();
  document.getElementById('memMsg').textContent = r.ok ? `Kaydedildi (id=${data.id})` : `Hata: ${data.detail||'?'}`;
  if(r.ok) document.getElementById('memText').value='';
}
load(); setInterval(load, 5000);
</script>
</body>
</html>"""


@app.get("/", response_class=HTMLResponse)
def index():
    return _INDEX_HTML


@app.get("/reactor", response_class=HTMLResponse)
def reactor_page():
    html = Path(__file__).resolve().parent / "reactor.html"
    if html.exists():
        return html.read_text(encoding="utf-8")
    return "<h1>reactor.html bulunamadı</h1>"


@app.get("/api/state")
def api_state():
    try:
        import sys
        sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
        from core.live_state import snapshot
        return snapshot()
    except Exception as e:
        return {"error": str(e)}


@app.websocket("/ws/state")
async def ws_state(ws: WebSocket):
    await ws.accept()
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from core.live_state import snapshot
    try:
        while True:
            await ws.send_json(snapshot())
            await asyncio.sleep(1 / 15)   # ~15 Hz
    except WebSocketDisconnect:
        return
    except Exception:
        return


def serve(host: str = "127.0.0.1", port: int = 8765):
    """Bloklu — ayrı thread'de çağrılır.
    log_config=None: uvicorn'un kendi logging dictConfig'i frozen (PyInstaller)
    ortamında 'default' formatter'ı çözemiyor; kendi log setup'ımızı kullanıyoruz.
    """
    import uvicorn
    uvicorn.run(app, host=host, port=port, log_config=None, access_log=False)
