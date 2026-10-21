from __future__ import annotations

import re
import time
import uuid
from collections.abc import Callable
from typing import Any, Literal

from agent.state import Evidence, Gap, RequirementSpec, RunState, SkillEvidence, TraceRow
from agent.tools.build_schedule import build_schedule, score_gaps
from agent.tools.estimate_effort import estimate_effort
from agent.tools.plan_validity import check_plan
from ontology.canonicalizer import find_mentions
from ontology.graph import SKILLS, adjacent, ancestors

LEVEL = {"aware": 0, "can_use": 1, "can_build": 2, "can_design": 3}
LEVEL_LABELS = {
    "aware": "awareness only",
    "can_use": "can use the skill",
    "can_build": "can build or deliver work with the skill",
    "can_design": "can design systems or approaches with the skill",
}


def _trace(
    s: RunState,
    node: str,
    ms: int | None = None,
    on_node: Callable[[dict[str, Any]], None] | None = None,
) -> None:
    now = time.perf_counter()
    elapsed_ms = max(0, round((now - s._last_trace_at) * 1000)) if ms is None else ms
    s._last_trace_at = now
    row = TraceRow(
        node=node, latency_ms=elapsed_ms, model="offline-fixture", prompt_version=f"{node}.v1"
    )
    s.trace.append(row)
    if on_node:
        on_node({"event": "node_end", "node": row.model_dump()})


def run_pipeline(
    profile_text: str,
    jd_text: str,
    weeks: int = 8,
    hours_per_week: float = 6,
    student_id: str = "demo-student",
    on_node: Callable[[dict[str, Any]], None] | None = None,
    requirements_override: list[RequirementSpec] | None = None,
    extra_trace: list[TraceRow] | None = None,
    degraded_reason: str | None = None,
    discovery_tier: str | None = None,
    profile_evidence_override: list[SkillEvidence] | None = None,
) -> RunState:
    s = RunState(
        run_id=str(uuid.uuid4()),
        student_id=student_id,
        jd_text=jd_text,
        profile_text=profile_text,
        weeks=weeks,
        hours_per_week=hours_per_week,
    )
    _trace(s, "intake", on_node=on_node)
    s.discovery_tier = discovery_tier or "role_archetype"
    _trace(s, "jd_discovery", on_node=on_node)
    # Fixture extraction: only recognized ontology skill names/aliases are eligible; source spans are exact.
    if extra_trace:
        s.trace.extend(extra_trace)
    if degraded_reason:
        s.degraded = True
        s.degraded_reasons.append(degraded_reason)
    seen = set()
    if requirements_override is not None:
        s.requirements = requirements_override
    else:
        for start, end, skill in find_mentions(jd_text):
            raw = jd_text[start:end]
            sid = skill["id"]
            if sid not in seen:
                seen.add(sid)
                quote = jd_text[start:end]
                hard = not bool(
                    re.search(
                        r"preferred|nice to have|bonus", jd_text[max(0, start - 60) : start].lower()
                    )
                )
                s.requirements.append(
                    RequirementSpec(
                        skill_text=raw,
                        skill_id=sid,
                        hard=hard,
                        required_level="can_build",
                        evidence=Evidence(
                            source_doc_id="job_description",
                            char_span=(start, end),
                            quote=quote,
                            extractor_confidence=0.88,
                        ),
                        confidence=0.88,
                    )
                )
    _trace(s, "jd_extract", on_node=on_node)
    if not s.requirements:
        s.degraded = True
        s.degraded_reasons.append("No canonical skills found in JD; using empty requirement set.")
    # Preserve source spans and match skills only when present in the student's actual text.
    if profile_evidence_override is not None:
        records = profile_evidence_override
        s.profile_cache_hit = True
        for node in ("profile_parse", "profile_normalize"):
            row = TraceRow(
                node=node,
                model="profile-store",
                prompt_version=f"{node}.v1",
                cache_status="hit",
            )
            s.trace.append(row)
            if on_node:
                on_node({"event": "node_end", "node": row.model_dump(mode="json")})
    else:
        prof = s.profile_text
        records = []
        for start, end, skill in find_mentions(prof):
            lvl = (
                "can_build"
                if re.search(
                    r"built|implemented|developed|deployed",
                    prof[max(0, start - 90) : end + 90],
                    re.IGNORECASE,
                )
                else "can_use"
            )
            records.append(
                SkillEvidence(
                    skill_id=skill["id"],
                    level=lvl,
                    evidence=[
                        Evidence(
                            source_doc_id="student_profile",
                            char_span=(start, end),
                            quote=prof[start:end],
                            extractor_confidence=0.83,
                        )
                    ],
                )
            )
        _trace(s, "profile_parse", on_node=on_node)
        _trace(s, "profile_normalize", on_node=on_node)
    s.evidence = records
    prof_map = {e.skill_id: e for e in records}
    for req in s.requirements:
        direct = prof_map.get(req.skill_id)
        related_ids = ancestors(req.skill_id) | adjacent(req.skill_id)
        related = [prof_map[a] for a in related_ids if a in prof_map]
        related_skill_names = sorted(
            {
                str(SKILLS.get(item.skill_id, {}).get("canonical_name", item.skill_id))
                for item in related
            },
            key=str.casefold,
        )
        skill_name = str(SKILLS.get(req.skill_id, {}).get("canonical_name", req.skill_text))
        target_level = LEVEL_LABELS.get(req.required_level, req.required_level.replace("_", " "))
        if direct and LEVEL[direct.level] >= LEVEL[req.required_level]:
            verdict: Literal["has", "partial", "missing"] = "has"
            level = direct.level
            ev = direct.evidence
            evidence_basis: Literal["direct", "related", "none"] = "direct"
            rationale = (
                f"Direct evidence found: your resume names {skill_name}. The current offline "
                f"matcher reads this as {LEVEL_LABELS.get(level, level.replace('_', ''))}; "
                f"it treats a skill mention as practical build evidence only when a nearby "
                f"action verb such as built, implemented, developed, or deployed is present. "
                f"The role marks this skill {'required' if req.hard else 'preferred'} and asks for "
                f"{target_level}, so the detected level meets this target."
            )
        elif direct:
            verdict = "partial"
            level = direct.level
            ev = direct.evidence
            evidence_basis = "direct"
            rationale = (
                f"Direct mention found: your resume names {skill_name}, but the current offline "
                f"matcher reads the surrounding wording as {LEVEL_LABELS.get(level, level.replace('_', ''))}. "
                f"The role marks this skill {'required' if req.hard else 'preferred'} and asks for "
                f"{target_level}. Add a concrete example of how you used or built with it to "
                "show stronger evidence."
            )
        elif related:
            verdict = "partial"
            level = max((e.level for e in related), key=lambda x: LEVEL[x])
            ev = [e for r in related for e in r.evidence]
            evidence_basis = "related"
            rationale = (
                f"No direct mention of {skill_name} was found. Your resume does mention related "
                f"skills ({', '.join(related_skill_names[:4])}), which may transfer but do not "
                f"prove this specific skill. The role marks it {'required' if req.hard else 'preferred'} "
                f"and asks for {target_level}."
            )
        else:
            verdict = "missing"
            level = "aware"
            ev = []
            evidence_basis = "none"
            rationale = (
                f"No direct or related mention of {skill_name} was found in the resume text we "
                f"could read. The role marks it {'required' if req.hard else 'preferred'} and asks "
                f"for {target_level}. This is a resume-evidence gap, not a conclusion that you "
                "do not have the skill."
            )
        delta = max(0, LEVEL[req.required_level] - LEVEL[level])
        effort = estimate_effort(req.skill_id, level, req.required_level)
        s.gaps.append(
            Gap(
                skill_id=req.skill_id,
                verdict=verdict,
                required_level=req.required_level,
                demonstrated_level=level,
                level_delta=delta,
                evidence=ev,
                rationale=rationale,
                evidence_basis=evidence_basis,
                related_skills=related_skill_names if evidence_basis == "related" else [],
                effort_hours=effort,
                hard=req.hard,
                market_demand_weight=float(
                    SKILLS.get(req.skill_id, {}).get("market_demand_weight", 0.5)
                ),
            )
        )
    _trace(s, "gap_analysis", on_node=on_node)
    s.gaps = score_gaps(s.gaps)
    _trace(s, "prioritize", on_node=on_node)
    s.plan = build_schedule(s.gaps, weeks, hours_per_week)
    _trace(s, "plan_build", on_node=on_node)
    check_plan(s.gaps, s.plan, s.weeks, s.hours_per_week)
    _trace(s, "critic", on_node=on_node)
    _trace(s, "human_approval", on_node=on_node)
    return s
