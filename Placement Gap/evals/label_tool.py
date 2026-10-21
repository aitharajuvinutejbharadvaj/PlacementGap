import argparse
import json

from evals.generate_data import ROOT, generate


def main() -> int:
    p = argparse.ArgumentParser(description="Print or edit labels for a dataset pair")
    p.add_argument("pair_id")
    p.add_argument("--split", default="dev")
    p.add_argument("--set-verdict", nargs=2, metavar=("SKILL_ID", "VERDICT"))
    a = p.parse_args()
    generate()
    f = ROOT / a.split / "pairs.json"
    rows = json.loads(f.read_text())
    row = next((x for x in rows if x["id"] == a.pair_id), None)
    if row is None:
        raise SystemExit("unknown pair id")
    if a.set_verdict:
        sid, v = a.set_verdict
        for x in row["labels"]["required_skills"]:
            if x["skill_id"] == sid:
                x["expected_verdict"] = v
                break
        f.write_text(json.dumps(rows, indent=2))
    print(json.dumps(row, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
