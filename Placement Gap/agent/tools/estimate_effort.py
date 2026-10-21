LEVEL = {"aware": 0, "can_use": 1, "can_build": 2, "can_design": 3}


def estimate_effort(skill_id: str, from_level: str, to_level: str) -> float:
    return float(max(1, LEVEL.get(to_level, 1) - LEVEL.get(from_level, 0)) * 6)
