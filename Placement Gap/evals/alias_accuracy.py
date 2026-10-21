from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path

from ontology.canonicalizer import canonicalize


def main() -> int:
    path = Path(__file__).resolve().parents[1] / "ontology" / "data" / "alias_tests.json"
    cases = json.loads(path.read_text(encoding="utf-8"))
    totals: dict[str, list[int]] = defaultdict(lambda: [0, 0])
    for case in cases:
        match = canonicalize(case["text"])
        totals[match.method][0] += 1
        totals[match.method][1] += int(match.skill_id == case["skill_id"])
    print(json.dumps({k: {"cases": v[0], "correct": v[1], "accuracy": v[1] / v[0]} for k, v in totals.items()}, indent=2))
    if sum(v[1] for v in totals.values()) / len(cases) < 0.95:
        raise SystemExit("Alias accuracy fell below the 95% ontology gate")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
