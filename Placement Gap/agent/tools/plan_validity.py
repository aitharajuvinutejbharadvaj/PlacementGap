from agent.state import Gap, PlanItem
from ontology.graph import ancestors


def check_plan(
    gaps: list[Gap], plan: list[PlanItem], weeks: int, hours_per_week: float
) -> dict[str, object]:
    violations: list[str] = []
    active = [p for p in plan if p.status == "scheduled"]
    if sum(p.hours for p in active) > weeks * hours_per_week + 1e-6:
        violations.append("total_hours")
    if len({p.skill_id for p in active}) != len(active):
        violations.append("duplicate_skill")
    for p in active:
        for pre in ancestors(p.skill_id):
            dep = next((x for x in active if x.skill_id == pre), None)
            if dep and dep.week >= p.week:
                violations.append("prerequisite_order")
                break
    for w in range(1, weeks + 1):
        load = sum(p.hours for p in active if p.week == w)
        if load and not (0.8 * hours_per_week <= load <= 1.2 * hours_per_week):
            violations.append("weekly_load")
            break
    covered = {p.skill_id for p in plan}
    deferred = {p.skill_id for p in plan if p.status == "deferred"}
    if any(
        g.verdict != "has" and g.skill_id not in covered and g.skill_id not in deferred
        for g in gaps
    ):
        violations.append("unaccounted_gap")
    return {"valid": not violations, "violations": sorted(set(violations))}
