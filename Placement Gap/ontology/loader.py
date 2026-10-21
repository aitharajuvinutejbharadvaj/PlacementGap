from __future__ import annotations

import json
from pathlib import Path
from typing import Any, cast

ROOT = Path(__file__).parent / "data"


def load_skills() -> list[dict[str, Any]]:
    p = ROOT / "skills.json"
    return cast(list[dict[str, Any]], json.loads(p.read_text(encoding="utf-8")))
