import io
import time

import pytest
from fastapi.testclient import TestClient
from reportlab.pdfgen import canvas

from api import main as api


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setattr(api, "DB", tmp_path / "runs.sqlite3")
    monkeypatch.setattr(api, "DATA", tmp_path)
    conn = api.db()
    cursor = conn.execute(
        "INSERT INTO users(email,name,password_salt,password_hash,created,email_verified) VALUES(?,?,?,?,?,1)",
        ("test@example.com", "Test User", "", "", time.time()),
    )
    conn.commit()
    test_user_id = str(cursor.lastrowid)
    conn.close()
    with TestClient(api.app) as test_client:
        test_client.cookies.set(
            "placementgap_session",
            api._encode_session({"sub": test_user_id, "email": "test@example.com", "name": "Test User"}),
        )
        yield test_client


def test_run_api_requires_valid_account_session():
    with TestClient(api.app) as anonymous:
        assert anonymous.get("/runs/example").status_code == 401
        assert anonymous.get("/health").status_code == 200
        assert anonymous.get("/auth/session").json() == {"user": None}


def test_manual_account_registration_login_and_logout(tmp_path, monkeypatch):
    monkeypatch.setattr(api, "DB", tmp_path / "accounts.sqlite3")
    monkeypatch.setattr(api, "_mail_settings", lambda: ("test-resend-key", "test@example.com"))
    sent_tokens = []
    monkeypatch.setattr(
        api,
        "_send_verification_email",
        lambda recipient, name, token, site_url: sent_tokens.append(token),
    )
    monkeypatch.setattr(api, "_send_login_notification", lambda *args: None)
    with TestClient(api.app) as account_client:
        created = account_client.post(
            "/auth/register",
            json={"name": "Alex Morgan", "email": "Alex@example.com", "password": "safe-pass-123"},
        )
        assert created.status_code == 202
        assert created.json()["email"] == "alex@example.com"
        assert not created.cookies.get("placementgap_session")
        assert account_client.get("/auth/session").json() == {"user": None}
        assert len(sent_tokens) == 1
        assert account_client.post(
            "/auth/register",
            json={"name": "Alex Morgan", "email": "alex@example.com", "password": "safe-pass-123"},
        ).status_code == 409
        account_client.cookies.clear()
        assert account_client.get("/runs/example").status_code == 401
        assert account_client.post(
            "/auth/login", json={"email": "alex@example.com", "password": "wrong-pass"}
        ).status_code == 401
        assert account_client.post(
            "/auth/login", json={"email": "alex@example.com", "password": "safe-pass-123"}
        ).status_code == 403
        verified = account_client.post("/auth/verify", json={"token": sent_tokens[0]})
        assert verified.status_code == 200
        logged_in = account_client.post(
            "/auth/login", json={"email": "ALEX@example.com", "password": "safe-pass-123"}
        )
        assert logged_in.status_code == 200
        assert account_client.get("/auth/session").json()["user"]["email"] == "alex@example.com"
        account_client.post("/auth/logout")
        assert account_client.get("/auth/session").json() == {"user": None}


def test_registration_requires_email_delivery_configuration(tmp_path, monkeypatch):
    monkeypatch.setattr(api, "DB", tmp_path / "accounts.sqlite3")
    monkeypatch.setattr(api, "_mail_settings", lambda: None)
    with TestClient(api.app) as account_client:
        response = account_client.post(
            "/auth/register",
            json={"name": "Alex Morgan", "email": "alex@example.com", "password": "safe-pass-123"},
        )
    assert response.status_code == 503
    assert "email verification is not configured" in response.json()["detail"].lower()
    conn = api.db()
    user_count = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    conn.close()
    assert user_count == 0


def test_session_cookie_is_signed_and_expires():
    cookie = api._encode_session({"sub": "u1", "email": "u@example.com", "name": "User"})
    assert api._decode_session(cookie) == {"sub": "u1", "email": "u@example.com", "name": "User"}
    assert api._decode_session(cookie + "bad") is None


def test_role_catalog_returns_every_selectable_role(client):
    response = client.get("/roles/catalog")
    assert response.status_code == 200
    roles = response.json()
    branches = client.get("/roles/branches")
    assert branches.status_code == 200
    assert len(roles) == sum(branch["role_count"] for branch in branches.json()) == 108
    assert {branch["name"] for branch in branches.json()} >= {
        "Computer Science & IT",
        "Electronics & Communication",
        "Electrical Engineering",
        "Mechanical Engineering",
        "Civil Engineering",
        "Chemical Engineering",
    }
    assert {item["role"] for item in roles} >= {
        "software engineer",
        "data analyst",
        "product manager",
        "cybersecurity analyst",
        "structural engineer",
        "process engineer",
    }


def test_run_review_and_report_flow(client):
    response = client.post(
        "/runs",
        json={
            "profile_text": "Built a Python project and used PostgreSQL.",
            "jd_text": "We need Python, SQL, React, and Docker skills.",
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
    gaps = {gap["skill_id"]: gap for gap in detail["state"]["gaps"]}
    assert gaps["python"]["verdict"] == "has"
    assert gaps["sql"]["verdict"] == "partial"
    assert gaps["sql"]["evidence_basis"] == "related"
    assert "PostgreSQL" in gaps["sql"]["related_skills"]
    assert gaps["docker"]["verdict"] == "missing"
    assert sum(
        item["hours"] for item in detail["state"]["plan"] if item["status"] == "scheduled"
    ) <= 20
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


@pytest.mark.parametrize("extension", [".txt", ".pdf", ".docx"])
def test_resume_upload_parses_supported_formats(client, extension):
    resume_text = "Built a Python service to process engineering data."
    if extension == ".txt":
        content = resume_text.encode("utf-8")
        content_type = "text/plain"
    elif extension == ".pdf":
        output = io.BytesIO()
        document = canvas.Canvas(output)
        document.drawString(72, 720, resume_text)
        document.save()
        content = output.getvalue()
        content_type = "application/pdf"
    else:
        try:
            from docx import Document
        except (ImportError, OSError) as exc:
            pytest.skip(f"DOCX dependency is unavailable in this environment: {exc}")
        output = io.BytesIO()
        document = Document()
        document.add_paragraph(resume_text)
        document.save(output)
        content = output.getvalue()
        content_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"

    started = client.post(
        "/runs/upload",
        files={"profile_file": (f"resume{extension}", content, content_type)},
        data={"jd_text": "Role requires Python.", "weeks": "4", "hours_per_week": "5"},
    )
    assert started.status_code == 202, started.text
    run_id = started.json()["run_id"]
    for _ in range(100):
        detail = client.get(f"/runs/{run_id}").json()
        if detail["status"] != "running":
            break
        time.sleep(0.03)
    assert detail["status"] == "awaiting_approval", detail
    assert "Python" in detail["state"]["profile_text"]
    assert any(
        gap["skill_id"] == "python" and gap["verdict"] == "has"
        for gap in detail["state"]["gaps"]
    )
