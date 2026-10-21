"""Typed data contracts. Pydantic v2 is used when installed; dataclass fallback supports offline demos."""

from __future__ import annotations

import time
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, PrivateAttr


class Contract(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Evidence(Contract):
    source_doc_id: str
    char_span: tuple[int, int]
    quote: str
    extractor_confidence: float = 1.0


class RequirementSpec(Contract):
    skill_text: str
    skill_id: str
    hard: bool = True
    required_level: str = "can_use"
    years_hint: float | None = None
    evidence: Evidence | None = None
    confidence: float = 1.0


class SkillEvidence(Contract):
    skill_id: str
    level: str
    evidence: list[Evidence] = Field(default_factory=list)


class Gap(Contract):
    skill_id: str
    verdict: Literal["has", "partial", "missing"]
    required_level: str
    demonstrated_level: str
    level_delta: int
    evidence: list[Evidence] = Field(default_factory=list)
    rationale: str = ""
    evidence_basis: Literal["direct", "related", "none"] = "none"
    related_skills: list[str] = Field(default_factory=list)
    effort_hours: float = 4.0
    score: float = 0.0
    hard: bool = True
    market_demand_weight: float = 0.6


class PlanItem(Contract):
    skill_id: str
    week: int
    hours: float
    objective: str
    resources: list[str] = Field(default_factory=list)
    status: str = "scheduled"
    deferred_reason: str | None = None


class TraceRow(Contract):
    node: str
    model: str = "fixture"
    prompt_version: str = "none"
    tokens_in: int = 0
    tokens_out: int = 0
    cost_usd: float = 0.0
    latency_ms: int = 0
    retry_count: int = 0
    cache_status: str = "miss"
    tool: str | None = None
    status: str = "ok"


class RunState(Contract):
    _last_trace_at: float = PrivateAttr(default_factory=time.perf_counter)
    run_id: str
    student_id: str
    jd_text: str
    profile_text: str
    weeks: int = 8
    hours_per_week: float = 6.0
    requirements: list[RequirementSpec] = Field(default_factory=list)
    evidence: list[SkillEvidence] = Field(default_factory=list)
    gaps: list[Gap] = Field(default_factory=list)
    plan: list[PlanItem] = Field(default_factory=list)
    trace: list[TraceRow] = Field(default_factory=list)
    degraded: bool = False
    degraded_reasons: list[str] = Field(default_factory=list)
    discovery_tier: str = "fixture"
    profile_cache_hit: bool = False
