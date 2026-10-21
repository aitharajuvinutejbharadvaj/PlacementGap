import time

import pytest
from fastapi.testclient import TestClient

from api import main as api


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setattr(api, "DB", tmp_path / "runs.sqlite3")
    monkeypatch.setattr(api, "DATA", tmp_path)
    with TestClient(api.app) as test_client:
        test_client.cookies.set(
            "placementgap_session",
            api._encode_session({"sub": "test-user", "email": "test@example.com", "name": "Test User"}),
        )
        yield test_client


def test_run_api_requires_valid_account_session():
    with TestClient(api.app) as anonymous:
        assert anonymous.get("/runs/example").status_code == 401
        assert anonymous.get("/health").status_code == 200
        assert anonymous.get("/auth/session").json() == {"user": None}


def test_manual_account_registration_login_and_logout(tmp_path, monkeypatch):
    monkeypatch.setattr(api, "DB", tmp_path / "accounts.sqlite3")
    with TestClient(api.app) as account_client:
        created = account_client.post(
            "/auth/register",
            json={"name": "Alex Morgan", "email": "Alex@example.com", "password": "safe-pass-123"},
        )
        assert created.status_code == 201
        assert created.json()["user"]["email"] == "alex@example.com"
        assert created.cookies.get("placementgap_session")
        assert account_client.get("/auth/session").json()["user"]["name"] == "Alex Morgan"
        assert account_client.post(
            "/auth/register",
            json={"name": "Alex Morgan", "email": "alex@example.com", "password": "safe-pass-123"},
        ).status_code == 409
        account_client.cookies.clear()
        assert account_client.get("/runs/example").status_code == 401
        assert account_client.post(
            "/auth/login", json={"email": "alex@example.com", "password": "wrong-pass"}
        ).status_code == 401
        logged_in = account_client.post(
            "/auth/login", json={"email": "ALEX@example.com", "password": "safe-pass-123"}
        )
        assert logged_in.status_code == 200
        assert account_client.get("/auth/session").json()["user"]["email"] == "alex@example.com"
        account_client.post("/auth/logout")
        assert account_client.get("/auth/session").json() == {"user": None}


def test_session_cookie_is_signed_and_expires():
    cookie = api._encode_session({"sub": "u1", "email": "u@example.com", "name": "User"})
    assert api._decode_session(cookie) == {"sub": "u1", "email": "u@example.com", "name": "User"}
    assert api._decode_session(cookie + "bad") is None


def test_role_catalog_returns_every_selectable_role(client):
    response = client.get("/roles/catalog")
    assert response.status_code == 200
    roles = response.json()
    assert len(roles) == 18
    assert {item["role"] for item in roles} >= {
        "software engineer",
        "data analyst",
        "product manager",
        "cybersecurity analyst",
    }


def test_run_review_and_report_flow(client):
    response = client.post(
        "/runs",
        json={
            "profile_text": "Built a Python project and used PostgreSQL.",
            "jd_text": "We need Python, React, and Docker skills.",
            "weeks": 4,
            "hours_per_week": 5,
        },
    )
    assert response.status_code == 202
    run_id = response.json()["run_id"]
    for _ in range(100):
        detail = client.get(f"/runs/{run_id}").json()
        if detail["status"] != "running":
            break
        time.sleep(0.03)
    assert detail["status"] == "awaiting_approval", detail
    assert detail["state"]["gaps"]
    events = client.get(f"/runs/{run_id}/stream").text
    assert "event: node_end" in events and "event: interrupt" in events
    approved = client.post(f"/runs/{run_id}/approve", json={"decision": "approve"})
    assert approved.status_code == 200, approved.text
    assert approved.json()["status"] == "approved"
    assert client.get(f"/runs/{run_id}/report.pdf").content.startswith(b"%PDF")


def test_role_search_accepts_seeded_examples(client):
    response = client.post(
        "/runs",
        json={
            "profile_text": "Completed Python coursework",
            "jd_role": "data analyst",
            "company": "Sample Analytics",
        },
    )
    assert response.status_code == 202
    run_id = response.json()["run_id"]
    for _ in range(100):
        detail = client.get(f"/runs/{run_id}").json()
        if detail["status"] != "running":
            break
        time.sleep(0.03)
    assert detail["status"] == "awaiting_approval", detail
    assert detail["state"]["discovery_tier"] == "role_archetype"
    assert detail["state"]["profile_cache_hit"] is False
    repeated = client.post(
        "/runs",
        json={
            "profile_text": "Completed Python coursework",
            "jd_role": "data analyst",
            "company": "Sample Analytics",
        },
    )
    second_id = repeated.json()["run_id"]
    for _ in range(100):
        second = client.get(f"/runs/{second_id}").json()
        if second["status"] != "running":
            break
        time.sleep(0.03)
    assert second["status"] == "awaiting_approval", second
    assert second["state"]["profile_cache_hit"] is True
    rejected = client.post(
        f"/runs/{second_id}/approve", json={"decision": "reject", "note": "Reduce scope"}
    )
    assert rejected.status_code == 200
    assert client.get(f"/runs/{second_id}").json()["status"] == "rejected"
