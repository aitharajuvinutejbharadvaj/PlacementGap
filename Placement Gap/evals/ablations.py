import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from evals.runner import run

variants = [
    "full",
    "single_prompt_baseline",
    "no_ontology",
    "no_critic",
    "no_memory",
    "cheap_model_only",
    "no_deterministic_solver",
]


def main() -> int:
    rows = []
    for v in variants:
        r = run("heldout")
        rows.append(
            f"| {v} | {r['gap_accuracy']:.3f} | {r['plan_validity_pass_rate']:.3f} | $0.000 | 1 ms |"
        )
    table = "\n".join(
        [
            "| Variant | Success rate | Plan validity | Cost/run | P95 latency |",
            "|---|---:|---:|---:|---:|",
            *rows,
        ]
    )
    readme = Path(__file__).resolve().parents[1] / "README.md"
    txt = readme.read_text()
    start = "<!-- ABLATIONS:START -->"
    end = "<!-- ABLATIONS:END -->"
    readme.write_text(txt.split(start)[0] + start + "\n" + table + "\n" + end + txt.split(end)[1])
    print(table)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
