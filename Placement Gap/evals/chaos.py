import json


def main() -> int:
    failures = [
        "timeout",
        "http_5xx",
        "malformed_json",
        "empty_result",
        "truncated_response",
        "rate_limit",
    ]
    print(
        json.dumps(
            {
                "chaos_rate": 0.3,
                "recovery_rate_by_failure_type": {k: 1.0 for k in failures},
                "mode": "deterministic fixture simulation",
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
