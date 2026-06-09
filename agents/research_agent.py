"""Research agent — routine research/summaries (DeepSeek by default). Draft/analysis only."""

from __future__ import annotations

from agents.worker_base import WorkerAgent


class ResearchAgent(WorkerAgent):
    name = "research_agent"
    default_complexity = "normal"
    system_prompt = WorkerAgent.system_prompt + (
        " Role: research analyst. Produce concise, sourced-where-possible research notes and "
        "summaries for the SportsVersusNews team. Output is an internal draft for human review."
    )

    def build_user_prompt(self, state) -> str:
        return f"Research request: {state.user_request}\nReturn a concise research brief (bullet points)."
