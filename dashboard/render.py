"""Render the dashboard data dict into a single self-contained HTML page (no JS deps)."""

from __future__ import annotations

import html


def _esc(x) -> str:
    return html.escape(str(x))


def _section(title: str, rows_html: str) -> str:
    return f"<section><h2>{_esc(title)}</h2>{rows_html or '<p class=muted>(none)</p>'}</section>"


def _ul(items: list[str]) -> str:
    return "<ul>" + "".join(f"<li>{i}</li>" for i in items) + "</ul>" if items else ""


def render_html(data: dict) -> str:
    pend = data.get("pending_approvals", {"content": [], "actions": []})
    content_items = _ul([f"{_esc(c['id'])} — {_esc(c['skill'])} (risk {_esc(c['risk'])})" for c in pend["content"]])
    action_items = _ul([f"{_esc(a['id'])} — {_esc(a['action'])}" for a in pend["actions"]])
    drafts = _ul([f"{_esc(d['id'])}: {_esc(d['preview'])}" for d in data.get("draft_articles", [])])
    calendar = _ul([f"{_esc(s['when'])} — {_esc(s['status'])} ({_esc(s['review'])})" for s in data.get("content_calendar", [])])
    activity = _ul([f"{_esc(a['ts'])} — {_esc(a['route'])} via {_esc(a['model'])} → {_esc(a['status'])}"
                    for a in data.get("agent_activity", [])])
    todos = _ul([_esc(t) for t in data.get("owner_todo", [])])

    return f"""<!doctype html>
<html lang=en><head><meta charset=utf-8>
<meta name=viewport content="width=device-width, initial-scale=1">
<title>Sportsverse — Owner Dashboard</title>
<style>
 body{{font-family:system-ui,Segoe UI,Arial,sans-serif;margin:0;background:#0f1419;color:#e6edf3}}
 header{{background:#161b22;padding:16px 24px;border-bottom:1px solid #30363d}}
 h1{{margin:0;font-size:20px}} .muted{{color:#8b949e}}
 main{{display:grid;grid-template-columns:repeat(auto-fit,minmax(320px,1fr));gap:16px;padding:24px}}
 section{{background:#161b22;border:1px solid #30363d;border-radius:10px;padding:16px}}
 h2{{font-size:15px;margin:0 0 10px;color:#58a6ff}}
 ul{{margin:0;padding-left:18px}} li{{margin:4px 0;font-size:14px}}
 .pill{{display:inline-block;background:#1f6feb22;color:#58a6ff;border:1px solid #1f6feb55;border-radius:999px;padding:2px 10px;font-size:12px}}
 footer{{padding:16px 24px;color:#8b949e;font-size:12px}}
</style></head>
<body>
<header>
 <h1>Sportsverse — Owner Dashboard</h1>
 <p class=muted>{_esc(data.get('business',''))} · status: <span class=pill>{_esc(data.get('system_status',''))}</span>
 · cost this month: <span class=pill>${_esc(data.get('cost',{}).get('month_total_usd',0))}</span>
 · generated {_esc(data.get('generated',''))}</p>
 <p class=muted>Nothing publishes automatically. Approve via Telegram or the CLIs.</p>
</header>
<main>
 {_section('Owner to-do', todos)}
 {_section('Pending approvals — content', content_items)}
 {_section('Pending approvals — actions', action_items)}
 {_section('Draft articles/content', drafts)}
 {_section('Content calendar (scheduled, not posted)', calendar)}
 {_section('Recent agent activity', activity)}
</main>
<footer>Sportsverse operating core · read-only view · data also at <code>/data</code> (JSON)</footer>
</body></html>"""
