from __future__ import annotations

from ontology.engineering_catalog import load_role_catalog


def search_jds(
    role: str, company: str | None = None, location: str | None = None, n: int = 5
) -> list[dict[str, str]]:
    fixtures = load_role_catalog()
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
