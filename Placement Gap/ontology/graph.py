from __future__ import annotations

from .loader import load_skills

SKILLS = {x["id"]: x for x in load_skills()}
PREREQS: dict[str, list[str]] = {x["id"]: x.get("prerequisites", []) for x in SKILLS.values()}
ADJACENT: dict[str, list[str]] = {
    x["id"]: [edge["skill_id"] for edge in x.get("adjacent_to", [])] for x in SKILLS.values()
}


def ancestors(skill_id: str) -> set[str]:
    seen: set[str] = set()
    stack = list(PREREQS.get(skill_id, []))
    while stack:
        n = stack.pop()
        if n not in seen:
            seen.add(n)
            stack.extend(PREREQS.get(n, []))
    return seen


def depth(skill_id: str) -> int:
    return len(ancestors(skill_id))


def adjacent(skill_id: str) -> set[str]:
    return set(ADJACENT.get(skill_id, []))


RELATED: dict[str, set[str]] = {
    skill_id: ancestors(skill_id) | adjacent(skill_id) for skill_id in SKILLS
}
for _child_id in SKILLS:
    for _prerequisite_id in ancestors(_child_id):
        RELATED.setdefault(_prerequisite_id, set()).add(_child_id)
    for _neighbor_id in adjacent(_child_id):
        RELATED.setdefault(_neighbor_id, set()).add(_child_id)
        RELATED[_child_id].add(_neighbor_id)


def related(skill_id: str) -> set[str]:
    """Return prerequisite, specialization, and adjacent skills in either direction."""
    return set(RELATED.get(skill_id, set()))
