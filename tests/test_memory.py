"""Tests for the file-based MemoryManager (uses a temp store, no real data touched)."""

from memory.manager import MemoryManager, slugify


def test_slugify():
    assert slugify("Hello World!") == "hello-world"
    assert slugify("  Multiple   Spaces ") == "multiple-spaces"


def test_remember_and_get(tmp_path):
    mm = MemoryManager(store_dir=tmp_path)
    path = mm.remember(
        "Test Fact",
        "Sportsverse parent brand is Sportsverse.",
        mem_type="project",
        description="brand fact",
    )
    assert path.exists()
    mem = mm.get("Test Fact")
    assert mem is not None
    assert "Sportsverse" in mem.content
    assert mem.type == "project"


def test_list_recall_forget(tmp_path):
    mm = MemoryManager(store_dir=tmp_path)
    mm.remember("Platinum Clips", "Main media channel is Platinum Clips.", description="channel")
    assert "platinum-clips" in mm.list_memories()

    hits = mm.recall("media channel")
    assert any("platinum" in h.name for h in hits)

    assert mm.forget("Platinum Clips") is True
    assert mm.list_memories() == []
