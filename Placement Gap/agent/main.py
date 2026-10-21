from __future__ import annotations

import argparse
from pathlib import Path

from agent.graph import run_pipeline
from agent.tools.render_report import render_report

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("command", choices=["demo", "seed"])
    p.add_argument("--profile")
    p.add_argument("--jd")
    p.add_argument("--weeks", type=int, default=8)
    p.add_argument("--hours", type=float, default=6)
    a = p.parse_args()
    if a.command == "seed":
        return 0
    profile = (
        Path(a.profile).read_text(encoding="utf-8")
        if a.profile
        else "Completed Python programming and database systems coursework. Built a Flask web application with PostgreSQL and Git."
    )
    jd = (
        Path(a.jd).read_text(encoding="utf-8")
        if a.jd
        else "Seeking a software engineer with Python, SQL, React, Docker, Git, REST APIs, and testing skills. Preferred: Kubernetes and AWS."
    )
    state = run_pipeline(profile, jd, a.weeks, a.hours)
    paths = render_report(state, ROOT / "outputs" / "demo")
    print(f"Run {state.run_id}: {len(state.gaps)} gaps, {len(state.plan)} plan items")
    for k, v in paths.items():
        print(f"{k}: {v}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
