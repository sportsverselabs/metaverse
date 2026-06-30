"""Pillow thumbnail provider (V1a).

Generates a branded thumbnail PNG from a template + fields. The layout is computed by a pure function
(`build_layout`, fully testable) and only the final draw needs Pillow. If Pillow isn't installed the
provider reports not-configured and returns a clear reason — never a fake success.

Pillow is an optional dependency (`pip install Pillow`); the test suite does not require it.
"""

from __future__ import annotations

from creative.providers.base import ThumbnailProvider, ThumbnailResult

# Brand defaults (no external assets required).
_TEMPLATES = {
    "sports_basic": {"size": (1280, 720), "bg": (11, 18, 32),
                     "title": {"xy": (64, 300), "size": 84, "color": (255, 255, 255)},
                     "subtitle": {"xy": (64, 420), "size": 44, "color": (120, 200, 255)}},
}


def build_layout(template: str, fields: dict) -> dict:
    """Return a draw spec: {size, bg, texts:[{text, xy, size, color}]}. Pure — no Pillow needed."""
    tpl = _TEMPLATES.get(template) or _TEMPLATES["sports_basic"]
    texts = []
    if fields.get("title"):
        texts.append({"text": str(fields["title"]), **tpl["title"]})
    if fields.get("subtitle"):
        texts.append({"text": str(fields["subtitle"]), **tpl["subtitle"]})
    return {"size": tpl["size"], "bg": tpl["bg"], "texts": texts}


class PillowThumbnailProvider(ThumbnailProvider):
    name = "pillow"

    @property
    def configured(self) -> bool:
        try:
            import PIL  # noqa: F401
            return True
        except Exception:
            return False

    def generate(self, template: str, fields: dict, output: str) -> ThumbnailResult:
        if not self.configured:
            return ThumbnailResult(False, reason="Pillow not installed (pip install Pillow)")
        from pathlib import Path

        from PIL import Image, ImageDraw, ImageFont

        spec = build_layout(template, fields)
        img = Image.new("RGB", spec["size"], spec["bg"])
        draw = ImageDraw.Draw(img)
        for t in spec["texts"]:
            try:
                font = ImageFont.truetype("arial.ttf", t["size"])
            except Exception:
                font = ImageFont.load_default()
            draw.text(t["xy"], t["text"], fill=t["color"], font=font)
        out = Path(output)
        out.parent.mkdir(parents=True, exist_ok=True)
        img.save(out)
        return ThumbnailResult(True, output_path=str(out))
