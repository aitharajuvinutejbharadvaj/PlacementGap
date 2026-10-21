from __future__ import annotations

import json
from pathlib import Path


def search_jds(
    role: str, company: str | None = None, location: str | None = None, n: int = 5
) -> list[dict[str, str]]:
    fixtures = json.loads(
        (Path(__file__).resolve().parents[2] / "ontology" / "data" / "jd_fixtures.json").read_text(
            encoding="utf-8"
        )
    )
    q = role.casefold()
    matches = [
        x for x in fixtures if q in x["title"].casefold() or q in x.get("role", "").casefold()
    ]
    if company:
        matches = [
            x for x in matches if company.casefold() in x.get("company", "").casefold()
        ] or matches
    for item in matches:
        item["location"] = location or item.get("location", "Remote")
        if company:
            item["company"] = company
    return matches[: max(1, n)]
