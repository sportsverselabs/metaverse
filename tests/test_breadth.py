"""Tests for Phase-6 breadth: Knowledge Library, department skill packs, Whisper auto-captions."""

import json
from pathlib import Path

from creative.models import Caption
from creative.providers.whisper_captions import WhisperCaptionProvider
from knowledge_library.library import KnowledgeLibrary


# ---- Knowledge Library ----------------------------------------------- #
def test_knowledge_add_get_list_remove(tmp_path):
    lib = KnowledgeLibrary(tmp_path)
    eid = lib.add("idea", "NBA buzzer beaters compilation", body="angle: top 10 clutch shots",
                  tags=["nba", "shorts"], source="espn")
    assert lib.get(eid)["title"].startswith("NBA")
    assert len(lib.list()) == 1 and len(lib.list(kind="idea")) == 1 and lib.list(kind="article") == []
    assert lib.remove(eid) and lib.get(eid) is None


def test_knowledge_search_ranks_title(tmp_path):
    lib = KnowledgeLibrary(tmp_path)
    lib.add("idea", "NBA clutch shots", tags=["nba"])
    lib.add("note", "random hockey note", body="mentions nba once nba")
    hits = lib.search("nba clutch")
    assert hits and hits[0]["title"] == "NBA clutch shots"   # title match outranks body
    assert all("score" in h for h in hits)
    assert lib.search("") == []


# ---- Department skill packs ------------------------------------------ #
def test_packs_registered_and_allowlisted():
    from skills.registry import default_registry
    from skills.packs import ALL_PACK_SKILLS, DEPARTMENT_PACKS
    reg = default_registry()
    names = set(reg.names())
    # every new pack skill is registered
    for cls in ALL_PACK_SKILLS:
        assert cls.spec.name in names
    # every name referenced by a department pack resolves to a registered skill
    for dept, skills in DEPARTMENT_PACKS.items():
        for s in skills:
            assert s in names, f"{dept} references unknown skill {s}"
    # all new pack skills are allowlisted (draft-only)
    allow = json.loads(Path("config/openclaw_allowlist.json").read_text(encoding="utf-8"))["skills"]
    for cls in ALL_PACK_SKILLS:
        assert allow.get(cls.spec.name, {}).get("allowed") is True


def test_new_departments_in_agent_directory():
    from agents.documentation_agent import AGENT_DIRECTORY
    for dept in ("creative_department", "marketing_department", "community_department",
                 "commerce_department", "technology_scout", "knowledge_library"):
        assert dept in AGENT_DIRECTORY


# ---- Whisper auto-captions (injected; no model download) ------------- #
def test_whisper_provider_injected():
    prov = WhisperCaptionProvider(transcriber=lambda p: [(0.0, 1.5, "hello"), (1.5, 3.0, "world")])
    assert prov.configured is True
    cues = prov.transcribe("anything.mp4")
    assert len(cues) == 2 and isinstance(cues[0], Caption) and cues[0].text == "hello"


def test_whisper_not_configured_returns_empty(monkeypatch):
    prov = WhisperCaptionProvider()  # no injected transcriber
    # Force "not installed" regardless of the environment.
    monkeypatch.setattr(WhisperCaptionProvider, "configured", property(lambda self: False))
    assert prov.transcribe("x.mp4") == []


def test_studio_auto_caption_action(tmp_path, monkeypatch):
    from dashboard import studio
    import creative.providers.whisper_captions as wc
    s = studio.VideoProjectStore(tmp_path / "video")
    monkeypatch.setattr(studio, "_store", lambda: s)

    class _FakeWhisper:
        configured = True
        def transcribe(self, path):
            return [Caption(0.0, 2.0, "auto one"), Caption(2.0, 4.0, "auto two")]
    monkeypatch.setattr(wc, "WhisperCaptionProvider", _FakeWhisper)

    pid = studio.studio_action({"action": "demo"})["project"]
    cid = s.load(pid).clips[0].id
    res = studio.studio_action({"action": "auto_caption", "project": pid, "clip": cid})
    assert "Auto-captioned 2" in res["message"]
    assert s.load(pid).clips[0].captions[0].text == "auto one"


# ---- Studio -> YouTube bridge (#3; upload itself still needs owner creds) ---- #
def test_youtube_bridge_enriches_video_post(tmp_path, monkeypatch):
    import creative.store as cs
    from creative.models import VideoProject
    from creative.store import VideoProjectStore
    from publishing.service import PublishingService
    from review.models import make_review_item

    store = VideoProjectStore(tmp_path / "video")
    p = VideoProject(title="My Clip")
    p.description = "desc"
    (store.root / p.id).mkdir(parents=True, exist_ok=True)
    (store.root / p.id / "render_draft.mp4").write_bytes(b"x")
    p.add_render(str(store.root / p.id / "render_draft.mp4"))
    store.save(p)
    monkeypatch.setattr(cs, "VideoProjectStore", lambda *a, **k: store)

    content = f"VIDEO PROJECT: My Clip\n\ndesc\n\nRender (local draft): x\nProject id: {p.id}\nCaptions: "
    item = make_review_item(skill="video_project", content=content, risk_score=0,
                            compliance={"passed": True}, compliance_passed=True)
    post = PublishingService._post_from_item(item, "youtube")
    assert post["title"] == "My Clip"
    assert post["video_path"].endswith("render_draft.mp4")
    assert post["description"] == "desc"
