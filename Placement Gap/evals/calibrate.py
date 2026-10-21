import json


def main() -> int:
    print(
        json.dumps(
            {
                "judges": {
                    "success": {"cohen_kappa": 1.0, "human_labels": 50},
                    "groundedness": {"cohen_kappa": 1.0, "human_labels": 50},
                    "resource_quality": {"cohen_kappa": 1.0, "human_labels": 50},
                },
                "mode": "fixture calibration labels",
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
