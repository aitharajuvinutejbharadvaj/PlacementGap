import json
import random
from pathlib import Path

from ontology.loader import load_skills

ROOT = Path(__file__).parent / "datasets"


def generate() -> None:
    random.seed(41)
    skills = load_skills()
    pairs = []
    for i in range(100):
        chosen = random.sample(skills, 5)
        prof = (
            "Student academic record. "
            + ". ".join(
                f"Completed {x['canonical_name']} coursework"
                if j < 2
                else f"Built and implemented a project using {x['canonical_name']}"
                for j, x in enumerate(chosen[:4])
            )
            + "."
        )
        jd = (
            "We seek a candidate skilled in "
            + ", ".join(x["canonical_name"] for x in chosen)
            + ". Preferred experience with "
            + chosen[-1]["canonical_name"]
            + "."
        )
        pairs.append(
            {
                "id": f"pair-{i + 1:03d}",
                "profile": prof,
                "jd": jd,
                "labels": {
                    "required_skills": [
                        {
                            "skill_id": x["id"],
                            "hard": j < 4,
                            "expected_verdict": "partial"
                            if j < 2
                            else ("has" if j < 4 else "missing"),
                        }
                        for j, x in enumerate(chosen)
                    ],
                    "acceptable_plan": {"max_hours": 48},
                },
            }
        )
    for split, rows in [
        ("dev", pairs[:60]),
        ("heldout", pairs[60:80]),
        ("adversarial", pairs[80:]),
    ]:
        d = ROOT / split
        d.mkdir(parents=True, exist_ok=True)
        (d / "pairs.json").write_text(json.dumps(rows, indent=2), encoding="utf-8")


if __name__ == "__main__":
    generate()
