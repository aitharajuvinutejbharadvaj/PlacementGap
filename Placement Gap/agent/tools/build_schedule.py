from __future__ import annotations

from agent.state import Gap, PlanItem
from agent.tools.find_resources import find_resources
from ontology.graph import ancestors, depth


def score_gaps(gaps: list[Gap]) -> list[Gap]:
    ids = {g.skill_id for g in gaps}
    out = []
    for g in gaps:
        weight = 1.0 if g.hard else 0.5
        demand = g.market_demand_weight
        bonus = 1.2 if any(g.skill_id in ancestors(i) for i in ids if i != g.skill_id) else 1.0
        g.score = weight * demand * max(1, g.level_delta) * bonus / max(g.effort_hours, 0.1)
        out.append(g)
    return sorted(out, key=lambda g: (-g.score, depth(g.skill_id), g.skill_id))


def build_schedule(gaps: list[Gap], weeks: int, hours_per_week: float) -> list[PlanItem]:
    if weeks < 1 or hours_per_week <= 0:
        raise ValueError("weeks and weekly hours must be positive")
    capacity = weeks * hours_per_week
    ordered = score_gaps([g for g in gaps if g.verdict != "has"])
    scheduled: dict[str, PlanItem] = {}
    out: list[PlanItem] = []
    used = 0.0
    for g in ordered:
        if g.skill_id.startswith("unresolved::"):
            out.append(
                PlanItem(
                    skill_id=g.skill_id,
                    week=weeks,
                    hours=0,
                    objective=f"Resolve the unmapped requirement: {g.skill_id.removeprefix('unresolved::')}",
                    status="deferred",
                    deferred_reason="Requirement is outside the current skill ontology and needs manual mapping.",
                )
            )
            continue
        hours = min(max(1.0, g.effort_hours), max(1.0, hours_per_week))
        # Place prerequisites before the skill, while avoiding duplicate plan items.
        chain = [p for p in ancestors(g.skill_id) if p not in scheduled]
        chain.sort(key=depth)
        needs = chain + ([g.skill_id] if g.skill_id not in scheduled else [])
        demand = sum(min(hours, hours_per_week) for _ in needs)
        if used + demand > capacity:
            out.append(
                PlanItem(
                    skill_id=g.skill_id,
                    week=weeks,
                    hours=0,
                    objective=f"Study {g.skill_id}",
                    status="deferred",
                    deferred_reason="Insufficient total hour budget",
                )
            )
            continue
        for sid in needs:
            h = hours
            if sid == g.skill_id:
                prereq_weeks = [scheduled[p].week for p in ancestors(sid) if p in scheduled]
                if prereq_weeks:
                    used = max(used, max(prereq_weeks) * hours_per_week)
            used += h
            week = min(weeks, int((used - 0.001) // hours_per_week) + 1)
            item = PlanItem(
                skill_id=sid,
                week=week,
                hours=h,
                objective=f"Build demonstrated competence in {sid}",
                resources=[r["url"] for r in find_resources(sid, "aware", "can_build", h)],
            )
            scheduled[sid] = item
            out.append(item)
    return sorted(out, key=lambda x: (x.week, x.skill_id, x.status))
