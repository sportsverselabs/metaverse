"""Video agent — concepts, scripts, and metadata for short-form sports video. DRAFT only.

Produces a video draft package and sends it to the approval queue. It never renders, uploads,
or publishes a video. Recommends CapCut for simple editing; edited files are uploaded back via
the approval agent.
"""

from __future__ import annotations

from agents.worker_base import WorkerAgent

CAPCUT_NOTE = ("Recommended editing: CapCut (free; great for TikTok / Instagram Reels / YouTube "
               "Shorts). Export 9:16, <= 60s. Then upload the edited file back via the approval flow.")


class VideoAgent(WorkerAgent):
    name = "video_agent"
    default_complexity = "normal"
    system_prompt = WorkerAgent.system_prompt + (
        " Role: short-form sports video producer for SportsVersusNews. Output a DRAFT video "
        "package: concept, a 30-45s script (hook / build / payoff / CTA), a title, a description, "
        "5-8 hashtags, suggested length, and the target platform. Mark it DRAFT. Never publish."
    )

    def build_user_prompt(self, state) -> str:
        return (f"Video request: {state.user_request}\n"
                "Return a DRAFT video package: concept, 30-45s script outline, title, description, "
                "hashtags, suggested length, target platform.")

    def run(self, state):
        state = super().run(state)
        if state.output:
            state.output += f"\n\n[{CAPCUT_NOTE}]"
            state.task_meta = {**(state.task_meta or {}), "deliverable": "video_draft"}
        return state
