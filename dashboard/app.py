"""Dashboard UI: login + Telegram-2FA pages and the 14-section command-center shell.

Server-rendered HTML fragments per section (the client fetches and injects them). Honest:
sections needing integrations show clear "needs owner setup" / "placeholder" notes.
"""

from __future__ import annotations

import html

from dashboard.data import SECTIONS, DashboardData

_CSS = """
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:system-ui,'Segoe UI',Arial,sans-serif;background:#07080c;color:#e9edf5}
a{color:#19e3ff;text-decoration:none}
.login-wrap{min-height:100vh;display:grid;place-items:center;padding:24px}
.card{background:#11131b;border:1px solid #20242f;border-radius:16px;padding:32px;width:100%;max-width:380px}
.card h1{font-size:22px;font-weight:900;letter-spacing:.04em}
.card h1 span{color:#ff3b30}
.card p.sub{color:#8b93a7;font-size:13px;margin:6px 0 22px}
.card label{display:block;font-size:12px;color:#8b93a7;margin:14px 0 6px}
.card input{width:100%;background:#07080c;border:1px solid #20242f;border-radius:10px;padding:12px 14px;color:#e9edf5;font-size:15px}
.card input:focus{outline:none;border-color:#19e3ff}
.btn{width:100%;margin-top:20px;background:#ff3b30;color:#fff;border:0;border-radius:100px;padding:13px;font-weight:700;font-size:15px;cursor:pointer}
.btn:hover{background:#ff5249}
.err{color:#ff6b6b;font-size:13px;margin-top:14px}
.ok{color:#19e3ff;font-size:13px;margin-top:14px}
/* shell */
.layout{display:grid;grid-template-columns:240px 1fr;min-height:100vh}
.side{background:#0c0e15;border-right:1px solid #20242f;padding:20px 0;position:sticky;top:0;height:100vh;overflow:auto}
.side .brand{font-weight:900;letter-spacing:.05em;padding:0 22px 18px;font-size:18px}
.side .brand span{color:#ff3b30}
.side a{display:block;padding:11px 22px;color:#aeb6c7;font-size:14px;border-left:3px solid transparent;cursor:pointer}
.side a:hover{background:#11131b;color:#fff}
.side a.active{color:#fff;border-left-color:#ff3b30;background:#11131b}
.side .logout{margin-top:18px;color:#8b93a7;font-size:12px}
.main{padding:28px clamp(18px,3vw,40px)}
.main h2{font-size:24px;font-weight:900;margin-bottom:4px}
.main .muted{color:#8b93a7;font-size:13px;margin-bottom:22px}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(220px,1fr));gap:14px}
.tile{background:#11131b;border:1px solid #20242f;border-radius:12px;padding:16px}
.tile .k{font-size:12px;color:#8b93a7}.tile .v{font-size:26px;font-weight:800;margin-top:6px}
.st{display:flex;justify-content:space-between;align-items:center;background:#11131b;border:1px solid #20242f;border-radius:10px;padding:11px 14px;margin-bottom:8px;font-size:14px}
.dot{display:inline-block;width:9px;height:9px;border-radius:50%;margin-right:8px}
.dot.ok{background:#27d07a}.dot.warn{background:#ffd33a}.dot.off{background:#5b647a}
.row{background:#11131b;border:1px solid #20242f;border-radius:10px;padding:14px;margin-bottom:10px}
.row h4{font-size:15px}.row .meta{color:#8b93a7;font-size:12px;margin-top:4px}
.tag{display:inline-block;font-size:11px;color:#19e3ff;border:1px solid #19e3ff55;border-radius:100px;padding:2px 9px;margin-right:6px}
.note{background:#1a1410;border:1px solid #6b4d1f;border-radius:10px;padding:12px 14px;color:#ffd9a3;font-size:13px;margin:12px 0}
.btnsm{background:#1b2030;border:1px solid #2a3142;color:#e9edf5;border-radius:8px;padding:7px 12px;font-size:13px;cursor:pointer;margin-right:6px}
.btnsm:hover{border-color:#19e3ff}
.btnsm.danger:hover{border-color:#ff3b30;color:#ff8a82}
pre{white-space:pre-wrap;background:#0c0e15;border:1px solid #20242f;border-radius:10px;padding:14px;font-size:13px;color:#c7cdda;overflow:auto}
textarea{width:100%;background:#0c0e15;border:1px solid #20242f;border-radius:10px;padding:12px;color:#e9edf5;font-family:inherit;font-size:14px}
"""


def _page(title: str, body: str) -> str:
    return (f"<!doctype html><html lang=en><head><meta charset=utf-8>"
            f"<meta name=viewport content='width=device-width, initial-scale=1'>"
            f"<title>{html.escape(title)}</title><style>{_CSS}</style></head><body>{body}</body></html>")


def login_page(error: str = "") -> str:
    err = f"<p class=err>{html.escape(error)}</p>" if error else ""
    body = f"""<div class=login-wrap><form class=card method=post action=/dashboard/login>
      <h1>SPORTS<span>VERSE</span></h1><p class=sub>Owner sign-in</p>
      <label>Username</label><input name=user autocomplete=username autofocus>
      <label>Password</label><input name=password type=password autocomplete=current-password>
      <button class=btn type=submit>Continue</button>{err}
      <p class=sub style=margin-top:18px>A verification code will be sent to your Telegram.</p>
    </form></div>"""
    return _page("Sportsverse — Sign in", body)


def verify_page(error: str = "") -> str:
    err = f"<p class=err>{html.escape(error)}</p>" if error else ""
    body = f"""<div class=login-wrap><form class=card method=post action=/dashboard/verify>
      <h1>SPORTS<span>VERSE</span></h1><p class=sub>Enter the 6-digit code from Telegram</p>
      <label>Verification code</label><input name=code inputmode=numeric autocomplete=one-time-code autofocus>
      <button class=btn type=submit>Verify &amp; enter</button>{err}
      <p class=sub style=margin-top:18px>Code expires in 5 minutes.</p>
    </form></div>"""
    return _page("Sportsverse — Verify", body)


def shell_page(user: str) -> str:
    links = "".join(
        f"<a data-section='{key}' onclick=\"go('{key}')\">{html.escape(label)}</a>"
        for key, label in SECTIONS
    )
    body = f"""<div class=layout>
      <nav class=side>
        <div class=brand>SPORTS<span>VERSE</span></div>
        {links}
        <a class=logout href=/dashboard/logout>Log out ({html.escape(user)})</a>
      </nav>
      <main class=main id=main><h2>Loading…</h2></main>
    </div>
    <script>
    function setActive(s){{document.querySelectorAll('.side a[data-section]').forEach(function(a){{a.classList.toggle('active',a.dataset.section===s);}});}}
    function go(section){{
      setActive(section);
      var m=document.getElementById('main'); m.innerHTML='<h2>Loading…</h2>';
      fetch('/dashboard/api?section='+encodeURIComponent(section)).then(function(r){{return r.text();}})
        .then(function(htmlStr){{m.innerHTML=htmlStr; wire();}})
        .catch(function(){{m.innerHTML='<div class=note>Could not load this section.</div>';}});
    }}
    function wire(){{
      var f=document.getElementById('askForm');
      if(f){{f.onsubmit=function(e){{e.preventDefault();
        var out=document.getElementById('askOut'); out.textContent='Hermes is thinking… (DeepSeek)';
        var cmd=document.getElementById('askCmd').value;
        fetch('/dashboard/ask',{{method:'POST',headers:{{'Content-Type':'application/json'}},body:JSON.stringify({{command:cmd}})}})
          .then(function(r){{return r.json();}}).then(function(j){{out.textContent=j.report||j.error||'(no response)';}})
          .catch(function(){{out.textContent='Request failed.';}});
        return false;}};}}
    }}
    window.dashAction=function(id,action){{
      if(action==='schedule' && !confirm('Are you sure you want to clear this for scheduled publishing? (It still will NOT be posted.)')) return;
      var reason=''; if(action==='reject'){{reason=prompt('Reason for rejecting?')||'';}}
      var notes=''; if(action==='edit'){{notes=prompt('What should change?')||'';}}
      fetch('/dashboard/action',{{method:'POST',headers:{{'Content-Type':'application/json'}},
        body:JSON.stringify({{id:id,action:action,reason:reason,notes:notes}})}})
        .then(function(r){{return r.json();}}).then(function(j){{alert(j.message||j.error||'done');go('approvals');}})
        .catch(function(){{alert('Action failed.');}});
    }};
    go('home');
    </script>"""
    return _page("Sportsverse — Dashboard", body)


# ---- section fragments ----------------------------------------------- #
def _esc(x) -> str:
    return html.escape(str(x))


def render_section(name: str, data=None) -> str:
    d = data or DashboardData()
    s = d.section(name)
    fn = _RENDERERS.get(name)
    return fn(s) if fn else "<div class=note>Section not available.</div>"


def _r_home(s):
    sts = "".join(
        f"<div class=st><span><span class='dot {('ok' if x['state']=='ok' else 'off' if x['state']=='off' else 'warn')}'></span>{_esc(x['name'])}</span><span>{_esc(x['status'])}</span></div>"
        for x in s["statuses"])
    tiles = "".join(f"<div class=tile><div class=k>{_esc(k)}</div><div class=v>{_esc(v)}</div></div>" for k, v in [
        ("Pending content approvals", s["pending_content"]), ("Pending action approvals", s["pending_actions"]),
        ("Active jobs", s["active_jobs"]), ("Completed today", s["today_done"]),
        ("AI cost today", f"${s['cost_today']:.4f}"), ("AI cost month-to-date", f"${s['cost_mtd']:.4f}")])
    todos = "".join(f"<li>{_esc(t)}</li>" for t in s["todos"])
    errs = "".join(f"<li>{_esc(e)}</li>" for e in s["errors"])
    return (f"<h2>Home</h2><p class=muted>Live system status. Nothing publishes/spends without your approval.</p>"
            f"<div class=grid>{tiles}</div>"
            f"<h3 style='margin:24px 0 10px'>Components</h3>{sts}"
            f"<h3 style='margin:24px 0 10px'>Owner action items</h3><ul>{todos}</ul>"
            f"<h3 style='margin:24px 0 10px'>Errors &amp; warnings</h3><ul>{errs}</ul>")


def _r_ask(s):
    return ("<h2>Ask Hermes</h2><p class=muted>Type a normal command. Jarvis routes it to Hermes; "
            "DeepSeek by default (Nemotron only for complex reasoning). Drafts go to your approval queue — nothing is published.</p>"
            "<form id=askForm><textarea id=askCmd rows=3 placeholder=\"e.g. Make me 3 sports video ideas. / What needs my approval? / Draft a YouTube short but do not publish it.\"></textarea>"
            "<button class=btn style='max-width:200px;margin-top:12px' type=submit>Ask Hermes</button></form>"
            "<h3 style='margin:20px 0 10px'>Response</h3><pre id=askOut>Ask something above.</pre>")


def _approval_row(i):
    return (f"<div class=row><h4>{_esc(i['skill'])} — {_esc(i['id'])}</h4>"
            f"<div class=meta>risk {_esc(i.get('risk'))}/100</div>"
            f"<div style='margin-top:10px'>"
            f"<button class=btnsm onclick=\"dashAction('{_esc(i['id'])}','approve')\">Approve draft</button>"
            f"<button class=btnsm onclick=\"dashAction('{_esc(i['id'])}','edit')\">Request edits</button>"
            f"<button class='btnsm danger' onclick=\"dashAction('{_esc(i['id'])}','reject')\">Reject</button>"
            f"<button class=btnsm onclick=\"dashAction('{_esc(i['id'])}','schedule')\">Approve for scheduling</button>"
            f"</div></div>")


def _r_approvals(s):
    content = "".join(_approval_row(i) for i in s["content"]) or "<p class=muted>No content awaiting approval.</p>"
    actions = "".join(f"<div class=row><h4>{_esc(a['action'])} — {_esc(a['id'])}</h4></div>" for a in s["actions"]) or "<p class=muted>No gated actions pending.</p>"
    return (f"<h2>Approvals</h2><p class=muted>Approve / request edits / reject. \"Approve for scheduling\" asks for confirmation and still does NOT publish.</p>"
            f"<h3 style='margin:14px 0 10px'>Content</h3>{content}"
            f"<h3 style='margin:22px 0 10px'>Gated actions</h3>{actions}")


def _r_pipeline(s):
    rows = "".join(f"<div class=st><span>{_esc(x['stage'])}</span><span>{_esc(x.get('count'))}{(' · '+x['note']) if x.get('note') else ''}</span></div>" for x in s["stages"])
    return f"<h2>Content Pipeline</h2><p class=muted>Stages of content moving through the system.</p>{rows}"


def _r_video(s):
    tools = "".join(f"<li>{_esc(t)}</li>" for t in s["tools"])
    return (f"<h2>Video Review</h2><div class=note>{_esc(s['note'])}</div>"
            f"<h3 style='margin:16px 0 10px'>Recommended editing tools</h3><ul>{tools}</ul>")


def _r_publishing(s):
    rows = "".join(f"<div class=st><span>{_esc(c['platform'])}</span><span>{_esc(c['status'])}</span></div>" for c in s["connections"])
    return f"<h2>Publishing</h2><div class=note>{_esc(s['note'])}</div>{rows}"


def _r_analytics(s):
    if s.get("placeholder"):
        return f"<h2>Analytics</h2><div class=note>{_esc(s['note'])}</div><p class=muted>No analytics recorded yet.</p>"
    return f"<h2>Analytics</h2><div class=note>{_esc(s['note'])}</div><pre>{_esc(s['summary'])}</pre>"


def _r_reports(s):
    return (f"<h2>Reports</h2><h3 style='margin:6px 0 10px'>Daily</h3><pre>{_esc(s['daily'])}</pre>"
            f"<h3 style='margin:18px 0 10px'>Weekly</h3><pre>{_esc(s['weekly'])}</pre>")


def _r_agents(s):
    rows = "".join(f"<div class=row><h4>{_esc(a['name'])} <span class=tag>{_esc(a['status'])}</span></h4><div class=meta>{_esc(a['purpose'])}</div></div>" for a in s["agents"])
    return f"<h2>Agents</h2><p class=muted>Every agent and what it does.</p>{rows}"


def _r_security(s):
    rows = "".join(f"<div class=st><span>{_esc(f['check'])}</span><span>{_esc(f['severity'])}: {_esc(f['detail'])}</span></div>" for f in s["findings"])
    return f"<h2>Security</h2><p class=muted>Live security scan (secrets, backups, leaks).</p>{rows}"


def _r_costs(s):
    return (f"<h2>Costs</h2><div class=grid>"
            f"<div class=tile><div class=k>Today</div><div class=v>${s['today']:.4f}</div></div>"
            f"<div class=tile><div class=k>Month-to-date</div><div class=v>${s['month_to_date']:.4f}</div></div>"
            f"<div class=tile><div class=k>Monthly budget</div><div class=v>${_esc(s['monthly_budget'])}</div></div>"
            f"<div class=tile><div class=k>Per-task approval</div><div class=v>${_esc(s['per_task_threshold'])}</div></div></div>"
            f"<p class=muted style='margin-top:14px'>Over-budget tasks pause for your approval before any spend.</p>")


def _r_backups(s):
    g = s["github"]
    rows = "".join(f"<div class=st><span>{_esc(k)}</span><span>{_esc(v)}</span></div>" for k, v in g.items())
    return f"<h2>Backups</h2><p class=muted>Code is backed up to GitHub; secrets are excluded.</p>{rows}"


def _r_settings(s):
    rows = "".join(f"<div class=st><span>{_esc(k)}</span><span>{_esc(v)}</span></div>" for k, v in s.items() if k != "note")
    return f"<h2>Settings</h2><div class=note>{_esc(s['note'])}</div>{rows}"


def _r_manual(s):
    docs = "".join(f"<li>{_esc(p)}</li>" for p in s["docs"])
    agents = "".join(f"<div class=row><h4>{_esc(a['name'])}</h4><div class=meta>{_esc(a['purpose'])}</div></div>" for a in s["agents"])
    return f"<h2>System Manual</h2><p class=muted>Docs (in the repo):</p><ul>{docs}</ul><h3 style='margin:18px 0 10px'>Agent directory</h3>{agents}"


def _r_skills(s):
    def row(sk):
        meta = sk.get("purpose") or sk.get("capabilities") or ""
        extra = f" · risk {sk['risk']}" if sk.get("risk") else ""
        return (f"<div class=row><h4>{_esc(sk['skill'])}</h4>"
                f"<div class=meta>{_esc(sk['status'])}{_esc(extra)} · {_esc(sk.get('agent',''))}</div>"
                f"<div class=meta>{_esc(meta)}</div></div>")
    installed = "".join(row(sk) for sk in s["installed"]) or "<p class=muted>No skills installed.</p>"
    pending = "".join(row(sk) for sk in s["pending"])
    return (f"<h2>Skills</h2><div class=note>{_esc(s['note'])}</div>"
            f"<h3 style='margin:16px 0 10px'>Installed (OpenClaw approved)</h3>{installed}"
            f"<h3 style='margin:22px 0 10px'>Requested — pending review</h3>{pending}")


def _r_sports(s):
    if s.get("error"):
        return f"<h2>Sports Data</h2><div class=note>{_esc(s['error'])}</div>"
    def pdot(st):
        return "ok" if st in ("online",) else ("off" if st in ("unknown", "needs API key") else "warn")
    prov = "".join(
        f"<div class=st><span><span class='dot {pdot(p.get('state',''))}'></span>{_esc(name)}</span>"
        f"<span>{_esc(p.get('state','?'))}"
        + (f" · {p['consecutive_failures']} fails" if p.get('consecutive_failures') else "")
        + (f" · {p['last_latency_ms']}ms" if p.get('last_latency_ms') else "")
        + "</span></div>"
        for name, p in (s.get("providers") or {}).items())
    def game(g):
        return (f"<div class=row><h4>{_esc(g['away']['team'])} {_esc(g['away'].get('score') or '')} @ "
                f"{_esc(g['home']['team'])} {_esc(g['home'].get('score') or '')}</h4>"
                f"<div class=meta>{_esc(g.get('league',''))} · {_esc(g.get('status',''))}</div></div>")
    live = "".join(game(g) for g in s.get("live_games", [])) or "<p class=muted>No live games right now.</p>"
    upcoming = "".join(game(g) for g in s.get("upcoming_games", [])) or "<p class=muted>No upcoming games loaded.</p>"
    news = "".join(
        f"<div class=row><h4>{_esc(n['headline'])}</h4><div class=meta>{_esc(n.get('league',''))}</div></div>"
        for n in s.get("latest_news", [])) or "<p class=muted>No news loaded.</p>"
    def fgame(g):
        return (f"<div class=row><h4>{_esc(g.get('home'))} {_esc(g.get('score_home'))} – "
                f"{_esc(g.get('score_away'))} {_esc(g.get('away'))}</h4>"
                f"<div class=meta>{_esc(g.get('league',''))} · {_esc(g.get('status',''))}"
                + (f" {g['elapsed']}'" if g.get('elapsed') else "") + "</div></div>")
    flive = s.get("football_live") or []
    fstatus = s.get("football_status")
    football_block = ""
    if fstatus:
        football_block += (f"<div class=note>API-Football plan: {_esc(fstatus.get('plan'))} · "
                           f"requests today {_esc(fstatus.get('requests_today'))}/"
                           f"{_esc(fstatus.get('requests_limit'))}</div>")
    football_rows = "".join(fgame(g) for g in flive) or "<p class=muted>No live soccer matches right now.</p>"
    return (f"<h2>Sports Data</h2><p class=muted>ESPN + API-Football via the Sports Data Hub "
            f"(cached; serves last-known data if a provider is down). Agents read the Hub, never the APIs directly.</p>"
            f"<button class=btnsm onclick=\"go('sports')\">Manual refresh</button>"
            f"<h3 style='margin:18px 0 10px'>Providers</h3>{prov}"
            f"<h3 style='margin:22px 0 10px'>Live games (ESPN)</h3>{live}"
            f"<h3 style='margin:22px 0 10px'>Live soccer (API-Football)</h3>{football_block}{football_rows}"
            f"<h3 style='margin:22px 0 10px'>Upcoming</h3>{upcoming}"
            f"<h3 style='margin:22px 0 10px'>Latest news</h3>{news}")


_RENDERERS = {
    "home": _r_home, "ask": _r_ask, "approvals": _r_approvals, "pipeline": _r_pipeline,
    "video": _r_video, "publishing": _r_publishing, "analytics": _r_analytics, "reports": _r_reports,
    "agents": _r_agents, "skills": _r_skills, "sports": _r_sports, "security": _r_security,
    "costs": _r_costs, "backups": _r_backups, "settings": _r_settings, "manual": _r_manual,
}
