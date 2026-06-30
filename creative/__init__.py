"""Sportsverse Creative Studio (V1a — local render foundation).

Dashboard-native video/thumbnail editing, open-source/local first. V1a is the headless foundation:
a ``VideoProject`` model + store, and three provider interfaces with local implementations
(FFmpeg video editor, Pillow thumbnails, SRT captions). No UI and **nothing publishes** — renders
go to local files only. The dashboard Studio UI (V1b) and AI-revision/compliance loop (V1c) build on this.

See architecture/CREATIVE_STUDIO_PLAN.md.
"""

from creative.models import (Caption, Clip, Overlay, TitleCard, VideoProject,
                             STATUS_APPROVED, STATUS_DRAFT, STATUS_RENDERED)
from creative.store import VideoProjectStore

__all__ = ["VideoProject", "Clip", "Caption", "TitleCard", "Overlay", "VideoProjectStore",
           "STATUS_DRAFT", "STATUS_RENDERED", "STATUS_APPROVED"]
