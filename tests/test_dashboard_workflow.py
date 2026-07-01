"""Tests for the dashboard workflow fixes: render preflight/errors, thumbnail, pipeline/orphan repair.

All offline; nothing publishes.
"""

import pytest

from agents.dashboard_agent import DashboardAgent
from approval.approval_queue import ApprovalQueue
from creative.providers.ffmpeg_editor import (FfmpegVideoEditor, _error_summary, preflight)
import creative.providers.ffmpeg_editor as fe
from dashboard.data import DashboardData
from review.models import STATUS_READY, make_review_item
from review.reconcile import audit_actions, find_orphaned, reconcile
from review.store import ReviewStore


# ---- render preflight + readable errors ------------------------------ #
def test_render_preflight_catches_missing_input(tmp_path):
    spec = {"inputs": [{"path": str(tmp_path / "nope.mp4")}], "output": str(tmp_path / "out.mp4")}
    problems = preflight(spec)
    assert any("input file not found" in p for p in problems)


def test_render_preflight_passes_for_real_input(tmp_path):
    f = tmp_path / "a.mp4"
    f.write_bytes(b"x")
    assert preflight({"inputs": [{"path": str(f), "in": 0, "out": 5}], "output": str(tmp_path / "out.mp4")}) == []


def test_render_preflight_flags_bad_trim_and_output_dir(tmp_path):
    f = tmp_path / "a.mp4"
    f.write_bytes(b"x")
    probs = preflight({"inputs": [{"path": str(f), "in": 5, "out": 2}], "output": str(tmp_path / "missing" / "out.mp4")})
    assert any("trim is invalid" in p for p in probs)
    assert any("output folder does not exist" in p for p in probs)


def test_render_returns_readable_error_not_exit_code(tmp_path, monkeypatch):
    # Pretend ffmpeg is installed so preflight runs; missing input must yield a clear message, not "exit 254".
    monkeypatch.setattr(fe.shutil, "which", lambda name: "/usr/bin/ffmpeg")
    res = FfmpegVideoEditor().render({"inputs": [{"path": str(tmp_path / "missing.mp4")}],
                                      "output": str(tmp_path / "out.mp4")})
    assert not res.ok
    assert "input file not found" in res.reason
    assert "254" not in res.reason


def test_ffmpeg_error_summary_strips_banner():
    stderr = ("ffmpeg version 6.1.1-3ubuntu5 Copyright ...\nbuilt with gcc 13\nconfiguration: --enable-gpl\n"
              "libavutil 58. 29.100\nmissing.mp4: No such file or directory\n")
    summary = _error_summary(stderr)
    assert "No such file or directory" in summary
    assert "ffmpeg version" not in summary


# ---- thumbnail saved at project root + served ------------------------ #
def test_thumbnail_saved_at_project_root_and_served(tmp_path, monkeypatch):
    from creative.providers.pillow_thumbnail import PillowThumbnailProvider
    if not PillowThumbnailProvider().configured:
        pytest.skip("Pillow not installed in this environment")
    from creative.store import VideoProjectStore
    from dashboard import studio
    store = VideoProjectStore(tmp_path)
    monkeypatch.setattr(studio, "_store", lambda: store)
    p = studio._make_demo(store)
    res = studio.studio_action({"action": "thumbnail", "project": p.id})
    assert "error" not in res
    assert (tmp_path / p.id / "thumbnail.png").is_file()          # at project ROOT, not assets/
    served = studio.media_path(p.id, "thumbnail.png")             # media route resolves it by filename
    assert served and served[0].is_file()
    assert store.load(p.id).status != "published"                 # nothing published


# ---- pipeline counts reflect real review records --------------------- #
def test_pipeline_counts_reflect_review_statuses(tmp_path):
    rs = ReviewStore(base_dir=tmp_path / "rv")
    aq = ApprovalQueue(base_dir=tmp_path / "ap")
    rs.add(make_review_item("content_draft", "a draft body", 0))   # STATUS_READY
    d = DashboardData()
    d.dash = DashboardAgent(review_store=rs, approval_queue=aq)
    out = d.pipeline()
    stages = {x["stage"]: x["count"] for x in out["stages"]}
    assert stages["Drafting → Waiting approval"] == 1
    assert out["gated_actions_pending"] == 0


# ---- gated action linkage + orphan detection + repair ---------------- #
def test_orphaned_gated_action_detected_and_reconciled(tmp_path):
    aq = ApprovalQueue(base_dir=tmp_path / "ap")
    rs = ReviewStore(base_dir=tmp_path / "rv")
    req = aq.request("publish_content", "from a research task", task_id="task-x")
    audit = audit_actions(approval_queue=aq, review_store=rs)
    assert audit and audit[0]["orphaned"] is True                  # no backing draft
    assert find_orphaned(aq, rs)[0]["id"] == req.id
    result = reconcile(apply=True, approval_queue=aq, review_store=rs)
    assert req.id in result["rejected"]
    assert aq.list(status="pending") == []                          # cleared (reversible)


def test_linked_gated_action_is_not_orphaned(tmp_path):
    aq = ApprovalQueue(base_dir=tmp_path / "ap")
    rs = ReviewStore(base_dir=tmp_path / "rv")
    aq.request("publish_content", "linked", task_id="task-y")
    rs.add(make_review_item("content_draft", "body", 0, source_text="creative-studio: from task-y"))
    audit = audit_actions(approval_queue=aq, review_store=rs)
    assert audit[0]["orphaned"] is False


def test_reconcile_dry_run_does_not_reject(tmp_path):
    aq = ApprovalQueue(base_dir=tmp_path / "ap")
    rs = ReviewStore(base_dir=tmp_path / "rv")
    aq.request("publish_content", "orphan", task_id="task-z")
    result = reconcile(apply=False, approval_queue=aq, review_store=rs)
    assert result["rejected"] == [] and len(result["orphaned"]) == 1
    assert len(aq.list(status="pending")) == 1                      # nothing changed on dry run
