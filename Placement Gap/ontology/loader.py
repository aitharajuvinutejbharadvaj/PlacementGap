from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, cast

from .engineering_catalog import engineering_skill_names

ROOT = Path(__file__).parent / "data"


def load_skills() -> list[dict[str, Any]]:
    p = ROOT / "skills.json"
    records = cast(list[dict[str, Any]], json.loads(p.read_text(encoding="utf-8")))
    known_names = {
        re.sub(r"[^a-z0-9]+", " ", str(record["canonical_name"]).casefold()).strip()
        for record in records
    }
    aliases = {
        "finite element analysis": ["FEA", "finite element method"],
        "computational fluid dynamics": ["CFD"],
        "building information modeling": ["BIM"],
        "programmable logic controller programming": ["PLC programming"],
        "very large scale integration design": ["VLSI design", "VLSI"],
        "printed circuit board design": ["PCB design"],
        "radio frequency engineering": ["RF engineering"],
        "global positioning system surveying": ["GNSS surveying"],
        "heating ventilation and air conditioning": ["HVAC"],
        "computer aided design": ["CAD"],
    }
    for name in engineering_skill_names():
        normalized = re.sub(r"[^a-z0-9]+", " ", name.casefold()).strip()
        if normalized in known_names:
            continue
        skill_id = re.sub(r"[^a-z0-9]+", "_", normalized).strip("_")
        records.append(
            {
                "id": skill_id,
                "canonical_name": name,
                "category": "engineering",
                "aliases": [name, *aliases.get(normalized, [])],
                "description": f"Engineering practice used in branch-specific career profiles: {name}.",
                "market_demand_weight": 0.6,
                "prerequisites": [],
                "adjacent_to": [],
                "specializes": [],
            }
        )
        known_names.add(normalized)
    return records
