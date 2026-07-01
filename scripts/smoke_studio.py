"""End-to-end Creative Studio smoke test (run on the VPS where ffmpeg/Pillow are installed).

Exercises the real workflow: create demo -> render -> thumbnail -> verify files + previews + pipeline
consistency, and asserts nothing publishes. Prints PASS/FAIL per step and exits non-zero on any failure.

    python scripts/smoke_studio.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from core.console import enable_utf8_console


def main() -> int:
    enable_utf8_console()
    from creative.store import VideoProjectStore
    from dashboard import studio
    from dashboard.data import DashboardData

    ok = True

    def check(label, cond, extra=""):
        nonlocal ok
        ok = ok and bool(cond)
        print(f"[{'PASS' if cond else 'FAIL'}] {label}{(' — ' + extra) if extra else ''}")

    store = VideoProjectStore()

    # 1. Create a demo project (generates a real sample clip if ffmpeg present).
    p = studio._make_demo(store)
    pid = p.id
    proj = store.root / pid
    check("1. demo project created", proj.is_dir(), f"id={pid}, clip={p.clips[0].src}")

    # 2. Render draft.
    r = studio.studio_action({"action": "render", "project": pid})
    check("2. render draft succeeds", "error" not in r, r.get("message") or r.get("error"))

    # 3. Generate thumbnail.
    t = studio.studio_action({"action": "thumbnail", "project": pid})
    check("3. thumbnail generated", "error" not in t, t.get("message") or t.get("error"))

    # 4/7. Files exist on disk.
    check("4. render file exists", (proj / "render_draft.mp4").is_file())
    check("5. thumbnail file exists (project root)", (proj / "thumbnail.png").is_file())

    # 6/8. Editor shows a video preview + thumbnail image.
    html = studio.editor_html(pid)
    check("6. editor shows <video> preview", "<video" in html)
    check("7. editor shows <img> thumbnail", "<img" in html)

    # 9. Pipeline / approvals consistency.
    d = DashboardData()
    appr = d.approvals()
    check("8. no orphaned gated actions", appr.get("orphaned", 0) == 0, f"orphaned={appr.get('orphaned')}")
    pl = d.pipeline()
    published = next((x["count"] for x in pl["stages"] if x["stage"] == "Published"), None)

    # 10. Nothing published.
    reloaded = store.load(pid)
    no_public = all(rr.get("visibility") == "private" for rr in reloaded.renders)
    check("9. nothing published", published == 0 and no_public and reloaded.status != "published",
          f"published_count={published}, status={reloaded.status}")

    print("\nSMOKE:", "ALL PASS ✅" if ok else "FAILURES ❌")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
