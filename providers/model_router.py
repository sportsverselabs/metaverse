"""Cost-aware model router (Phase 4).

Chooses the model for a task and tracks spend:

- **DeepSeek** (default) for routine work: summaries, drafts, normal research, basic code edits,
  logs, recurring reports.
- **Nemotron** ONLY for complex reasoning, long-context/multimodal analysis, agent planning,
  high-value business decisions, and difficult coding architecture — and only if it is enabled
  and configured. Otherwise it gracefully falls back to DeepSeek.

It estimates tokens + cost per task, tracks monthly spend, and if an estimate exceeds the
per-task threshold or would blow the monthly budget, it returns ``needs_approval`` WITHOUT
calling the model (no spend) so the orchestration can route to a human approval gate first.

Mock mode (``LLM_MODE != live``) never hits the network and records zero spend.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Optional

from core import paths
from core.logging_setup import get_logger
from core.providers.base import LLMNotConfigured
from core.providers.mock import MockProvider
from providers.deepseek_provider import DeepSeekProvider
from providers.nemotron_provider import NemotronProvider

# Task types that warrant the heavier (Nemotron) model when it is available.
COMPLEX_TASK_TYPES = frozenset({
    "reasoning", "planning", "architecture", "long_context", "multimodal",
    "high_value_decision", "agent_planning",
})

_DEFAULT_BUDGET = {
    "monthly_budget_usd": 20.0,
    "per_task_approval_threshold_usd": 0.50,
    "assumed_completion_tokens": 600,
    "prices_per_1k_tokens": {
        "deepseek": {"input": 0.00027, "output": 0.0011},
        "nemotron": {"input": 0.001, "output": 0.003},
        "mock": {"input": 0.0, "output": 0.0},
    },
}


def _load_budget() -> dict:
    try:
        if paths.MODEL_BUDGET_FILE.exists():
            data = json.loads(paths.MODEL_BUDGET_FILE.read_text(encoding="utf-8"))
            merged = dict(_DEFAULT_BUDGET)
            merged.update({k: v for k, v in data.items() if not k.startswith("_")})
            return merged
    except (json.JSONDecodeError, OSError):
        pass
    return dict(_DEFAULT_BUDGET)


@dataclass
class ModelResult:
    text: str
    provider: str
    model: str
    est_tokens: int = 0
    est_cost: float = 0.0
    is_mock: bool = False
    needs_approval: bool = False
    note: str = ""


class CostTracker:
    """Tracks actual recorded spend per calendar month (file-based, gitignored)."""

    def __init__(self, ledger_path: Optional[Path] = None) -> None:
        self.path = ledger_path or (paths.LOGS_DIR / "cost_ledger.json")
        self.log = get_logger("cost")

    def _read(self) -> dict:
        try:
            if self.path.exists():
                return json.loads(self.path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            pass
        return {}

    def _write(self, data: dict) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(data, indent=2), encoding="utf-8")

    @staticmethod
    def _month() -> str:
        return date.today().strftime("%Y-%m")

    def month_total(self) -> float:
        return float(self._read().get(self._month(), 0.0))

    def add(self, cost: float) -> float:
        data = self._read()
        month = self._month()
        data[month] = round(float(data.get(month, 0.0)) + float(cost), 6)
        self._write(data)
        return data[month]


class ModelRouter:
    def __init__(self, config=None, budget: Optional[dict] = None,
                 cost_tracker: Optional[CostTracker] = None, logger=None) -> None:
        self.config = config
        self.budget = budget or _load_budget()
        self.cost_tracker = cost_tracker or CostTracker()
        self.log = logger or get_logger("model_router")
        self.mode = str((config.get("LLM_MODE") if config else None) or "mock").lower()
        self._deepseek = DeepSeekProvider(config)
        self._nemotron = NemotronProvider(config)
        self._mock = MockProvider(config)

    # ------------------------------------------------------------------ #
    @property
    def is_live(self) -> bool:
        return self.mode == "live"

    def nemotron_available(self) -> bool:
        return self._nemotron.available()

    def select(self, task_type: str, complexity: str = "normal") -> tuple[str, str]:
        """Return (provider_name, model_name). DeepSeek default; Nemotron for complex work."""
        wants_heavy = complexity == "complex" or task_type in COMPLEX_TASK_TYPES
        if wants_heavy and self._nemotron.available():
            return "nemotron", self._nemotron.model_name()
        # Default / fallback path.
        return "deepseek", self._deepseek.default_model

    # ------------------------------------------------------------------ #
    def estimate_tokens(self, prompt: str, system: Optional[str] = None) -> int:
        chars = len(prompt or "") + len(system or "")
        prompt_tokens = max(1, chars // 4)
        return prompt_tokens + int(self.budget.get("assumed_completion_tokens", 600))

    def estimate_cost(self, provider_name: str, est_tokens: int, system_len: int = 0) -> float:
        prices = self.budget.get("prices_per_1k_tokens", {}).get(provider_name, {"input": 0.0, "output": 0.0})
        completion = int(self.budget.get("assumed_completion_tokens", 600))
        prompt_tokens = max(0, est_tokens - completion)
        cost = (prompt_tokens / 1000.0) * prices.get("input", 0.0) + (completion / 1000.0) * prices.get("output", 0.0)
        return round(cost, 6)

    # ------------------------------------------------------------------ #
    def complete(self, prompt: str, *, task_type: str = "general", system: Optional[str] = None,
                 complexity: str = "normal") -> ModelResult:
        provider_name, model = self.select(task_type, complexity)
        est_tokens = self.estimate_tokens(prompt, system)
        est_cost = self.estimate_cost(provider_name, est_tokens)

        # Budget gating BEFORE any spend.
        threshold = float(self.budget.get("per_task_approval_threshold_usd", 0.50))
        monthly = float(self.budget.get("monthly_budget_usd", 0.0))
        over_task = est_cost > threshold
        over_month = monthly > 0 and (self.cost_tracker.month_total() + est_cost) > monthly
        if over_task or over_month:
            reason = []
            if over_task:
                reason.append(f"estimated ${est_cost:.4f} exceeds per-task threshold ${threshold:.2f}")
            if over_month:
                reason.append("would exceed monthly budget")
            self.log.info("Cost gate: approval required (%s)", "; ".join(reason))
            return ModelResult(text="", provider=provider_name, model=model, est_tokens=est_tokens,
                               est_cost=est_cost, is_mock=not self.is_live, needs_approval=True,
                               note="; ".join(reason))

        # Mock mode: no network, no spend.
        if not self.is_live:
            preview = " ".join((prompt or "").split())[:200]
            text = f"[MOCK {provider_name}/{model}] offline draft. Prompt preview: {preview}"
            return ModelResult(text=text, provider=provider_name, model=model, est_tokens=est_tokens,
                               est_cost=est_cost, is_mock=True, needs_approval=False)

        # Live: call the selected provider; fall back deepseek -> mock on any error.
        for prov_name in (provider_name, "deepseek"):
            prov = self._nemotron if prov_name == "nemotron" else self._deepseek
            if not prov.available():
                continue
            try:
                resp = prov.complete(prompt, system=system, model=(model if prov_name == provider_name else None))
                self.cost_tracker.add(est_cost)
                return ModelResult(text=resp.text, provider=prov_name, model=resp.model, est_tokens=est_tokens,
                                   est_cost=est_cost, is_mock=False, needs_approval=False)
            except LLMNotConfigured as exc:
                self.log.warning("Provider '%s' not configured (%s); trying fallback.", prov_name, exc)
            except Exception as exc:  # never crash on provider/network errors
                self.log.error("Provider '%s' error (%s); trying fallback.", prov_name, exc)

        # Everything unavailable -> safe mock.
        self.log.warning("No live provider usable; using mock (no spend).")
        preview = " ".join((prompt or "").split())[:200]
        return ModelResult(text=f"[MOCK fallback] {preview}", provider="mock", model="mock-1",
                           est_tokens=est_tokens, est_cost=0.0, is_mock=True, needs_approval=False)
