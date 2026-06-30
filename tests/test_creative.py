"""Creative Studio V1a tests — fully offline (no ffmpeg/Pillow/network required)."""

from creative.models import Caption, Clip, VideoProject, STATUS_RENDERED
from creative.providers.ffmpeg_editor import FfmpegVideoEditor, build_ffmpeg_command
from creative.providers.pillow_thumbnail import PillowThumbnailProvider, build_layout
from creative.providers.srt_captions import SrtCaptionProvider, format_srt, parse_srt
from creative.render import build_caption_cues, build_render_spec
from creative.store import VideoProjectStore


def _project():
    p = VideoProject(title="Test Recap")
    p.clips = [
        Clip(src="a.mp4", in_=0.0, out=5.0, order=0, captions=[Caption(0.0, 2.0, "Hook")]),
        Clip(src="b.mp4", in_=1.0, out=4.0, order=1, captions=[Caption(0.0, 1.5, "Finish")]),
    ]
    return p


# ---- model + store --------------------------------------------------- #
def test_ordered_clips_and_duration():
    p = _project()
    p.clips[0].order = 5  # reorder
    assert [c.src for c in p.ordered_clips()] == ["b.mp4", "a.mp4"]
    assert p.clips[0].duration == 5.0 and p.clips[1].duration == 3.0


def test_edit_history_append_only_and_render():
    p = _project()
    p.add_edit("owner", "trimmed clip", before=5.0, after=4.0)
    assert p.edit_history[-1]["actor"] == "owner" and p.edit_history[-1]["action"] == "trimmed clip"
    p.add_render("/tmp/out.mp4")
    assert p.status == STATUS_RENDERED and p.renders[0]["visibility"] == "private"


def test_store_roundtrip(tmp_path):
    store = VideoProjectStore(tmp_path)
    p = _project()
    store.save(p)
    loaded = store.load(p.id)
    assert loaded.title == p.title and len(loaded.clips) == 2
    assert loaded.clips[0].captions[0].text == "Hook"
    assert store.list_ids() == [p.id]


# ---- render spec + ffmpeg command ----------------------------------- #
def test_build_render_spec_orders_inputs():
    spec = build_render_spec(_project(), "out.mp4")
    assert [i["path"] for i in spec["inputs"]] == ["a.mp4", "b.mp4"]
    assert spec["inputs"][1]["in"] == 1.0 and spec["inputs"][1]["out"] == 4.0


def test_ffmpeg_command_trim_and_concat():
    spec = build_render_spec(_project(), "out.mp4")
    cmd = build_ffmpeg_command(spec)
    joined = " ".join(cmd)
    assert cmd[0] == "ffmpeg" and "-filter_complex" in cmd
    assert "trim=start=0.0:end=5.0" in joined and "trim=start=1.0:end=4.0" in joined
    assert "concat=n=2:v=1:a=1[vout][aout]" in joined
    assert cmd[-1] == "out.mp4"


def test_ffmpeg_command_with_captions_adds_subtitles():
    spec = build_render_spec(_project(), "out.mp4", captions_srt="c.srt")
    joined = " ".join(build_ffmpeg_command(spec))
    assert "concat=n=2:v=1:a=1[vcat][aout]" in joined and "subtitles=" in joined


def test_ffmpeg_editor_with_injected_runner():
    calls = {}
    def fake_runner(argv):
        calls["argv"] = argv
        return 0, ""
    ed = FfmpegVideoEditor(runner=fake_runner)
    assert ed.configured is True
    res = ed.render(build_render_spec(_project(), "out.mp4"))
    assert res.ok and res.output_path == "out.mp4" and calls["argv"][0] == "ffmpeg"


def test_ffmpeg_editor_reports_failure():
    ed = FfmpegVideoEditor(runner=lambda argv: (1, "boom"))
    res = ed.render(build_render_spec(_project(), "out.mp4"))
    assert not res.ok and "ffmpeg exited 1" in res.reason


# ---- captions -------------------------------------------------------- #
def test_caption_cues_offset_by_clip_durations():
    cues = build_caption_cues(_project())
    # clip a is 5s long, so clip b's caption (0..1.5) shifts to 5..6.5
    assert cues[0].start == 0.0 and cues[0].end == 2.0
    assert cues[1].start == 5.0 and cues[1].end == 6.5


def test_caption_cues_skipped_when_duration_unknown():
    p = _project()
    p.clips[0].out = None  # unknown duration
    assert build_caption_cues(p) == []


def test_srt_roundtrip():
    cues = [Caption(0.0, 2.5, "Line one"), Caption(2.5, 4.0, "Line two")]
    text = format_srt(cues)
    assert "00:00:00,000 --> 00:00:02,500" in text
    parsed = parse_srt(text)
    assert len(parsed) == 2 and parsed[1].text == "Line two" and parsed[1].start == 2.5


def test_srt_provider_writes_file(tmp_path):
    path = SrtCaptionProvider().write([Caption(0, 1, "hi")], tmp_path / "c.srt")
    assert "hi" in open(path, encoding="utf-8").read()


# ---- thumbnail ------------------------------------------------------- #
def test_thumbnail_layout_pure():
    layout = build_layout("sports_basic", {"title": "TOP PLAYS", "subtitle": "Tonight"})
    assert layout["size"] == (1280, 720)
    assert layout["texts"][0]["text"] == "TOP PLAYS" and len(layout["texts"]) == 2


def test_thumbnail_provider_configured_or_clear_reason(tmp_path):
    prov = PillowThumbnailProvider()
    res = prov.generate("sports_basic", {"title": "X"}, str(tmp_path / "t.png"))
    if prov.configured:
        assert res.ok and res.output_path
    else:
        assert not res.ok and "Pillow" in res.reason
