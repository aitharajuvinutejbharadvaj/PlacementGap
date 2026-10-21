from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from .loader import load_skills


def norm(s: str) -> str:
    language_token = s.strip().lower()
    language_match = re.fullmatch(r"(c\+\+|c#)(?:\s+(.*))?", language_token)
    if language_token == "c":
        return "c"
    if language_match:
        suffix = re.sub(r"[^a-z0-9]+", " ", language_match.group(2) or "").strip()
        return language_match.group(1) + (" " + suffix if suffix else "")
    return re.sub(r"[^a-z0-9]+", " ", s.lower()).strip()


@dataclass(frozen=True)
class CanonicalMatch:
    skill_id: str | None
    canonical_name: str | None
    confidence: float
    method: str
    raw: str


_skills = load_skills()
_canonical = {norm(x["canonical_name"]): x for x in _skills}
_aliases = {norm(a): x for x in _skills for a in x["aliases"]}
_mention_pattern: re.Pattern[str] | None = None


def canonicalize(text: str, context: str | None = None) -> CanonicalMatch:
    key = norm(text)
    if key in _canonical:
        x = _canonical[key]
        return CanonicalMatch(x["id"], x["canonical_name"], 1.0, "exact", text)
    if key in _aliases:
        x = _aliases[key]
        return CanonicalMatch(x["id"], x["canonical_name"], 0.98, "alias", text)
    # Token overlap is a deterministic offline fallback for close variants; it is never silent.
    toks = set(key.split())
    best = None
    score = 0.0
    if toks:
        for x in _skills:
            words = set(norm(x["canonical_name"]).split())
            overlap = len(toks & words) / max(len(toks | words), 1)
            if overlap > score:
                best, score = x, overlap
    if best is not None and score >= 0.8:
        return CanonicalMatch(best["id"], best["canonical_name"], score, "token", text)
    return CanonicalMatch(None, None, 0.0, "unresolved", text)


def find_mentions(text: str) -> list[tuple[int, int, dict[str, Any]]]:
    """Find exact canonical/alias occurrences, preferring the longest phrase."""
    import re

    global _mention_pattern
    pattern = _mention_pattern
    if pattern is None:
        aliases = sorted(_aliases.items(), key=lambda pair: -len(pair[0]))
        # A single longest-first expression avoids recompiling thousands of phrases per document.
        alternatives = [re.escape(a).replace(r"\ ", r"\s+") for a, _ in aliases if a]
        _mention_pattern = re.compile(
            r"(?<![A-Za-z0-9])(?:" + "|".join(alternatives) + r")(?![A-Za-z0-9])", re.IGNORECASE
        )
        pattern = _mention_pattern
    found: list[tuple[int, int, dict[str, Any]]] = []
    for m in pattern.finditer(text):
        hit = canonicalize(m.group())
        if hit.skill_id:
            skill = _canonical.get(norm(hit.canonical_name or ""), _aliases.get(norm(m.group())))
            if skill is not None:
                found.append((m.start(), m.end(), skill))
    return [(a, b, x) for a, b, x in found if x is not None]
