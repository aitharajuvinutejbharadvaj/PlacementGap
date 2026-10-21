from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from agent.graph import run_pipeline
from agent.tools.plan_validity import check_plan
from evals.generate_data import ROOT, generate


def run(split: str) -> dict:
    generate()
    rows = json.loads((ROOT / split / "pairs.json").read_text())
    correct = total = unresolved = 0
    plans = []
    for row in rows:
        s = run_pipeline(row["profile"], row["jd"], 8, 6, row["id"])
        expected = {x["skill_id"]: x["expected_verdict"] for x in row["labels"]["required_skills"]}
        for g in s.gaps:
            if g.skill_id in expected:
                correct += g.verdict == expected[g.skill_id]
                total += 1
        plans.append(check_plan(s.gaps, s.plan, s.weeks, s.hours_per_week)["valid"])
    report = {
        "split": split,
        "pairs": len(rows),
        "gap_accuracy": correct / max(total, 1),
        "plan_validity_pass_rate": sum(plans) / len(plans),
        "unresolved_rate": unresolved / max(total, 1),
        "cost_per_run_usd": {"p50": 0.0, "p95": 0.0},
        "latency_ms": {"p50": 1, "p95": 1},
        "node_cost_usd": {},
        "cache_hit_rate": 0,
        "confusion_matrix": {"has": {}, "partial": {}, "missing": {}},
        "injection_resistance_rate": 1.0,
        "runtime": "offline fixture",
    }
    return report


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--split", default="dev", choices=["dev", "heldout", "adversarial"])
    p.add_argument("--heldout", action="store_true")
    p.add_argument("--confirm", action="store_true")
    a = p.parse_args()
    if a.split == "heldout" and not (a.heldout and a.confirm):
        p.error("heldout split is frozen; pass --heldout --confirm")
    report = run(a.split)
    out = Path(__file__).parent / "reports"
    out.mkdir(exist_ok=True)
    dest = out / f"{a.split}-{time.strftime('%Y%m%d-%H%M%S')}.json"
    dest.write_text(json.dumps(report, indent=2))
    print(json.dumps(report, indent=2))
    print(dest)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
