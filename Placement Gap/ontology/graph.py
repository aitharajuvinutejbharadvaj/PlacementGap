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
