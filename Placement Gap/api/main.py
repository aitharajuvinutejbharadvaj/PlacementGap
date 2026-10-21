from __future__ import annotations

import asyncio
import base64
import hashlib
import hmac
import json
import os
import re
import secrets
import sqlite3
import time
import uuid
from collections.abc import AsyncIterator
from pathlib import Path
from time import perf_counter
from typing import Annotated, Any

from fastapi import FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse
from pydantic import BaseModel, Field

from agent.graph import run_pipeline
from agent.llm import extract_requirements
from agent.state import RunState, SkillEvidence, TraceRow
from agent.tools.build_schedule import build_schedule
from agent.tools.fetch_url import fetch_url
from agent.tools.parse_document import parse_document
from agent.tools.render_report import render_report
from agent.tools.search_jds import search_jds
from memory.profile_store import ProfileStore
from ontology.canonicalizer import find_mentions

ROOT = Path(__file__).resolve().parents[1]


def _load_local_env() -> None:
    env_file = ROOT / ".env"
    if env_file.exists():
        for line in env_file.read_text(encoding="utf-8").splitlines():
            key, separator, value = line.partition("=")
            if separator and key.strip() and not key.lstrip().startswith("#"):
                os.environ.setdefault(key.strip(), value.strip().strip("\"'"))


_load_local_env()
SESSION_SECRET = os.getenv("PLACEMENTGAP_SESSION_SECRET") or secrets.token_urlsafe(48)
DATA = ROOT / "outputs" / "app"
DATA.mkdir(parents=True, exist_ok=True)
DB = DATA / "runs.sqlite3"
app = FastAPI(title="PlacementGap", version="0.2.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)


def _encode_session(user: dict[str, str]) -> str:
    payload = json.dumps({**user, "exp": int(time.time()) + 60 * 60 * 24 * 7}, separators=(",", ":"))
    encoded = base64.urlsafe_b64encode(payload.encode()).decode().rstrip("=")
    signature = hmac.new(SESSION_SECRET.encode(), encoded.encode(), hashlib.sha256).digest()
    return encoded + "." + base64.urlsafe_b64encode(signature).decode().rstrip("=")


def _decode_session(value: str | None) -> dict[str, str] | None:
    if not value or "." not in value:
        return None
    encoded, supplied = value.rsplit(".", 1)
    expected = base64.urlsafe_b64encode(
        hmac.new(SESSION_SECRET.encode(), encoded.encode(), hashlib.sha256).digest()
    ).decode().rstrip("=")
    if not hmac.compare_digest(supplied, expected):
        return None
    try:
        payload = encoded + "=" * (-len(encoded) % 4)
        user = json.loads(base64.urlsafe_b64decode(payload))
        if user.get("exp", 0) < time.time():
            return None
        return {k: str(user[k]) for k in ("sub", "email", "name")}
    except (ValueError, KeyError, TypeError):
        return None


@app.middleware("http")
async def require_account_session(request: Request, call_next):  # type: ignore[no-untyped-def]
    path = request.url.path
    if path.startswith("/api/"):
        path = path[4:]
    if path in {"/health", "/auth/register", "/auth/login", "/auth/session", "/auth/logout"}:
        return await call_next(request)
    if not _decode_session(request.cookies.get("placementgap_session")):
        return JSONResponse({"detail": "Sign in or create an account to continue."}, status_code=401)
    return await call_next(request)


def db() -> sqlite3.Connection:
    conn = sqlite3.connect(DB, timeout=15)
    conn.row_factory = sqlite3.Row
    conn.execute(
        "CREATE TABLE IF NOT EXISTS runs (run_id TEXT PRIMARY KEY, status TEXT NOT NULL, state TEXT, paths TEXT, error TEXT, updated REAL NOT NULL)"
    )
    conn.execute(
        "CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY AUTOINCREMENT, email TEXT NOT NULL UNIQUE, name TEXT NOT NULL, password_salt TEXT NOT NULL, password_hash TEXT NOT NULL, created REAL NOT NULL)"
    )
    conn.commit()
    return conn


class RunRequest(BaseModel):
    profile_text: str = Field(default="", max_length=200_000)
    jd_text: str = Field(default="", max_length=100_000)
    jd_url: str | None = Field(default=None, max_length=2048)
    jd_role: str | None = Field(default=None, max_length=160)
    company: str | None = Field(default=None, max_length=160)
    location: str | None = Field(default=None, max_length=160)
    student_id: str = "student"
    weeks: int = Field(default=8, ge=1, le=52)
    hours_per_week: float = Field(default=6, gt=0, le=80)


class Approval(BaseModel):
    decision: str
    note: str = ""
    weeks: int | None = Field(default=None, ge=1, le=52)
    hours_per_week: float | None = Field(default=None, gt=0, le=80)


class RegisterRequest(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    email: str = Field(min_length=3, max_length=254)
    password: str = Field(min_length=8, max_length=128)


class LoginRequest(BaseModel):
    email: str = Field(min_length=3, max_length=254)
    password: str = Field(min_length=1, max_length=128)


class GuideRequest(BaseModel):
    profile_text: str = Field(min_length=1, max_length=200_000)


def _lookup(run_id: str) -> sqlite3.Row:
    with db() as conn:
        row = conn.execute("SELECT * FROM runs WHERE run_id=?", (run_id,)).fetchone()
    if row is None:
        raise HTTPException(404, "run not found")
    return row


def _save(
    run_id: str,
    status: str,
    state: dict[str, Any] | None = None,
    paths: dict[str, str] | None = None,
    error: str | None = None,
) -> None:
    with db() as conn:
        conn.execute(
            "INSERT INTO runs(run_id,status,state,paths,error,updated) VALUES(?,?,?,?,?,?) ON CONFLICT(run_id) DO UPDATE SET status=excluded.status,state=excluded.state,paths=excluded.paths,error=excluded.error,updated=excluded.updated",
            (
                run_id,
                status,
                json.dumps(state) if state is not None else None,
                json.dumps(paths) if paths else None,
                error,
                time.time(),
            ),
        )


def _publish(run_id: str, event: dict[str, Any]) -> None:
    bus = EVENT_LOG.setdefault(run_id, [])
    bus.append(event)
    condition = EVENT_CONDITIONS.get(run_id)
    if condition:

        async def wake() -> None:
            async with condition:
                condition.notify_all()

        asyncio.get_running_loop().create_task(wake())


EVENT_LOG: dict[str, list[dict[str, Any]]] = {}
EVENT_CONDITIONS: dict[str, asyncio.Condition] = {}


async def _run_in_background(req: RunRequest, run_id: str) -> None:
    _publish(run_id, {"event": "run_start", "run_id": run_id})
    try:
        jd = req.jd_text
        discovery_tier = "pasted_text"
        if req.jd_url:
            fetched = await asyncio.to_thread(fetch_url, req.jd_url)
            jd = fetched["text"]
            discovery_tier = "live_url"
            _publish(
                run_id,
                {
                    "event": "tool_call",
                    "tool": "fetch_url",
                    "status": "ok",
                    "content_hash": fetched["content_hash"],
                },
            )
        elif not jd.strip() and req.jd_role:
            results = await asyncio.to_thread(search_jds, req.jd_role, req.company, req.location, 1)
            if not results:
                raise ValueError(
                    "No matching role fixture found. Paste a job description or use a supported role such as software engineer."
                )
            jd = results[0]["text"]
            discovery_tier = "role_archetype"
            _publish(
                run_id,
                {
                    "event": "tool_call",
                    "tool": "search_jds",
                    "status": "degraded",
                    "tier": discovery_tier,
                    "title": results[0]["title"],
                },
            )
        requirements, llm_trace, extraction_note = await extract_requirements(jd)
        if not req.profile_text.strip():
            raise ValueError("Add your academic record or upload a transcript/resume to continue.")
        loop = asyncio.get_running_loop()

        def emit(payload: dict[str, Any]) -> None:
            loop.call_soon_threadsafe(_publish, run_id, payload)

        profile_hash = hashlib.sha256(req.profile_text.encode("utf-8")).hexdigest()
        profiles = ProfileStore(DATA / "profiles.json")
        profile_store_note = None
        try:
            cached_profile = await asyncio.to_thread(profiles.get, req.student_id)
        except (OSError, ValueError) as exc:
            cached_profile = None
            profile_store_note = f"Profile cache read failed; parsed the submitted record again: {exc}"
        profile_evidence: list[SkillEvidence] | None = None
        if cached_profile and cached_profile.get("profile_hash") == profile_hash:
            try:
                profile_evidence = [
                    SkillEvidence.model_validate(item)
                    for item in cached_profile.get("evidence", [])
                ]
            except ValueError as exc:
                profile_evidence = None
                profile_store_note = f"Profile cache validation failed; parsed the submitted record again: {exc}"
        state = await asyncio.to_thread(
            run_pipeline,
            req.profile_text,
            jd,
            req.weeks,
            req.hours_per_week,
            req.student_id,
            emit,
            requirements,
            llm_trace,
            extraction_note,
            discovery_tier,
            profile_evidence,
        )
        state.run_id = run_id
        if profile_store_note:
            state.degraded = True
            state.degraded_reasons.append(profile_store_note)
        try:
            await asyncio.to_thread(
                profiles.put,
                req.student_id,
                {
                    "profile_hash": profile_hash,
                    "evidence": [item.model_dump(mode="json") for item in state.evidence],
                },
            )
        except (OSError, ValueError) as exc:
            state.degraded = True
            state.degraded_reasons.append(f"Profile cache write failed; this profile will be reparsed next run: {exc}")
        _save(run_id, "awaiting_approval", state.model_dump(mode="json"))
        _publish(run_id, {"event": "interrupt", "node": "human_approval", "run_id": run_id})
    except Exception as exc:  # noqa: BLE001 - background task must persist any failure for the client
        _save(run_id, "failed", error=f"{type(exc).__name__}: {exc}")
        _publish(run_id, {"event": "run_error", "message": str(exc)})


@app.post("/runs", status_code=202)
async def create_run(req: RunRequest) -> dict[str, str]:
    if not req.profile_text.strip():
        raise HTTPException(422, "profile_text is required (or use POST /runs/upload)")
    if not (req.jd_text.strip() or req.jd_url or req.jd_role):
        raise HTTPException(422, "Provide jd_text, jd_url, or jd_role")
    run_id = str(uuid.uuid4())
    EVENT_LOG[run_id] = []
    EVENT_CONDITIONS[run_id] = asyncio.Condition()
    _save(run_id, "running")
    asyncio.create_task(_run_in_background(req, run_id))
    return {"run_id": run_id, "status": "running"}


@app.post("/runs/upload", status_code=202)
async def create_run_upload(
    profile_file: UploadFile = File(...),  # noqa: B008 - FastAPI requires this declaration for multipart parsing
    jd_text: str = Form(""),
    jd_url: str = Form(""),
    student_id: str = Form("student"),
    weeks: int = Form(8),
    hours_per_week: float = Form(6),
    jd_role: str = Form(""),
    company: str = Form(""),
    location: str = Form(""),
) -> dict[str, str]:
    if profile_file.size is not None and profile_file.size > 20 * 1024 * 1024:
        raise HTTPException(413, "Profile uploads must be 20 MB or smaller")
    contents = await profile_file.read(20 * 1024 * 1024 + 1)
    if len(contents) > 20 * 1024 * 1024:
        raise HTTPException(413, "Profile uploads must be 20 MB or smaller")
    ext = Path(profile_file.filename or "").suffix.lower()
    kind = {".pdf": "pdf", ".docx": "docx", ".txt": "text", ".md": "text"}.get(ext)
    if not kind:
        raise HTTPException(415, "Upload a PDF, DOCX, TXT, or Markdown file")
    try:
        parsed = await asyncio.to_thread(parse_document, contents, kind)
    except Exception as exc:
        raise HTTPException(422, f"Could not read the uploaded file: {exc}") from exc
    req = RunRequest(
        profile_text=parsed["text"],
        jd_text=jd_text,
        jd_url=jd_url or None,
        jd_role=jd_role or None,
        company=company or None,
        location=location or None,
        student_id=student_id,
        weeks=weeks,
        hours_per_week=hours_per_week,
    )
    return await create_run(req)


@app.get("/runs/{run_id}")
async def get_run(run_id: str) -> dict[str, Any]:
    row = _lookup(run_id)
    return {
        "run_id": run_id,
        "status": row["status"],
        "error": row["error"],
        "state": json.loads(row["state"]) if row["state"] else None,
    }


@app.get("/runs/{run_id}/trace")
async def get_trace(run_id: str) -> list[dict[str, Any]]:
    row = _lookup(run_id)
    return json.loads(row["state"]).get("trace", []) if row["state"] else EVENT_LOG.get(run_id, [])


@app.get("/runs/{run_id}/stream")
async def stream_run(run_id: str) -> StreamingResponse:
    _lookup(run_id)
    condition = EVENT_CONDITIONS.setdefault(run_id, asyncio.Condition())

    async def events() -> AsyncIterator[str]:
        index = 0
        while True:
            current = EVENT_LOG.get(run_id, [])
            while index < len(current):
                event = current[index]
                index += 1
                yield f"event: {event['event']}\ndata: {json.dumps(event)}\n\n"
                if event["event"] in {"interrupt", "run_error", "run_end"}:
                    return
            row = _lookup(run_id)
            if row["status"] in {"awaiting_approval", "approved", "rejected", "failed"}:
                if row["status"] == "awaiting_approval":
                    yield 'event: interrupt\ndata: {"node":"human_approval"}\n\n'
                return
            async with condition:
                try:
                    await asyncio.wait_for(condition.wait(), timeout=15)
                except TimeoutError:
                    yield ": keepalive\n\n"

    return StreamingResponse(
        events(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@app.post("/runs/{run_id}/approve")
async def approve_run(run_id: str, body: Approval) -> dict[str, Any]:
    row = _lookup(run_id)
    if row["status"] != "awaiting_approval" or not row["state"]:
        raise HTTPException(409, f"Run is {row['status']}; it is not waiting for review")
    state_data = json.loads(row["state"])
    state = RunState.model_validate(state_data)
    if body.decision == "reject":
        _save(run_id, "rejected", state_data)
        _publish(run_id, {"event": "run_end", "status": "rejected", "note": body.note})
        return {"run_id": run_id, "status": "rejected", "note": body.note}
    if body.decision not in {"approve", "edit"}:
        raise HTTPException(422, "decision must be approve, edit, or reject")
    if body.decision == "edit":
        state.weeks = body.weeks or state.weeks
        state.hours_per_week = body.hours_per_week or state.hours_per_week
        state.plan = build_schedule(state.gaps, state.weeks, state.hours_per_week)
        if body.note:
            state.degraded_reasons.append(f"Human plan edit: {body.note}")
    report_started = perf_counter()
    paths = render_report(state, DATA / "reports" / run_id)
    report_trace = TraceRow(
        node="report",
        model="deterministic-python",
        prompt_version="report.v1",
        latency_ms=round((perf_counter() - report_started) * 1000),
    )
    state.trace.append(report_trace)
    _publish(run_id, {"event": "node_end", "node": report_trace.model_dump(mode="json")})
    _save(run_id, "approved", state.model_dump(mode="json"), paths)
    _publish(run_id, {"event": "run_end", "status": "approved", "report": paths})
    return {"run_id": run_id, "status": "approved", "report": paths}


@app.get("/runs/{run_id}/report.{kind}")
async def get_report(run_id: str, kind: str) -> FileResponse:
    row = _lookup(run_id)
    if row["status"] != "approved" or not row["paths"]:
        raise HTTPException(409, "Approve the plan before downloading the report")
    names = {"md": "markdown", "pdf": "pdf", "json": "json"}
    if kind not in names:
        raise HTTPException(404, "report not found")
    path = Path(json.loads(row["paths"])[names[kind]])
    return FileResponse(
        path,
        media_type={"md": "text/markdown", "pdf": "application/pdf", "json": "application/json"}[
            kind
        ],
    )


@app.get("/runs/{a}/diff/{b}")
async def diff_runs(a: str, b: str) -> dict[str, Any]:
    left, right = _lookup(a), _lookup(b)
    ls = json.loads(left["state"] or "{}")
    rs = json.loads(right["state"] or "{}")
    return {
        "a": a,
        "b": b,
        "gap_verdicts": {
            "a": {g["skill_id"]: g["verdict"] for g in ls.get("gaps", [])},
            "b": {g["skill_id"]: g["verdict"] for g in rs.get("gaps", [])},
        },
        "plans": {"a": ls.get("plan", []), "b": rs.get("plan", [])},
    }


@app.get("/evals/latest")
async def eval_latest() -> dict[str, Any]:
    files = (
        sorted((ROOT / "evals" / "reports").glob("*.json"))
        if (ROOT / "evals" / "reports").exists()
        else []
    )
    return (
        json.loads(files[-1].read_text(encoding="utf-8"))
        if files
        else {"status": "no eval report generated"}
    )


@app.get("/health")
async def health() -> dict[str, str]:
    from agent.llm import available

    return {"status": "ok", "mode": "llm" if available() else "fixture"}


@app.get("/roles/catalog")
async def roles_catalog() -> list[dict[str, str]]:
    records = json.loads((ROOT / "ontology" / "data" / "jd_fixtures.json").read_text(encoding="utf-8"))
    return [
        {key: str(record[key]) for key in ("title", "role", "company", "location")}
        for record in records
    ]


def _career_recommendations(profile_text: str) -> dict[str, Any]:
    candidate_skills: dict[str, str] = {}
    for _, _, skill in find_mentions(profile_text):
        candidate_skills[skill["id"]] = skill["canonical_name"]
    if not candidate_skills:
        raise HTTPException(
            422,
            "We couldn't identify skills in that resume. Add a skills section, tools, projects, or experience details and try again.",
        )

    records = json.loads((ROOT / "ontology" / "data" / "jd_fixtures.json").read_text(encoding="utf-8"))
    recommendations: list[dict[str, Any]] = []
    for record in records:
        job_text = record["text"]
        required_marker = re.search(r"required skills include\s*", job_text, re.IGNORECASE)
        preferred_marker = re.search(r"(?:preferred|nice to have|bonus)\s*:\s*", job_text, re.IGNORECASE)
        if required_marker:
            required_text = job_text[required_marker.end() : preferred_marker.start() if preferred_marker else len(job_text)]
        else:
            required_text = job_text
        preferred_text = job_text[preferred_marker.end() :] if preferred_marker else ""

        required_skills: dict[str, str] = {}
        for _, _, skill in find_mentions(required_text):
            required_skills[skill["id"]] = skill["canonical_name"]
        preferred_skills: dict[str, str] = {}
        for _, _, skill in find_mentions(preferred_text):
            preferred_skills[skill["id"]] = skill["canonical_name"]

        matched_required = [name for skill_id, name in required_skills.items() if skill_id in candidate_skills]
        matched_preferred = [name for skill_id, name in preferred_skills.items() if skill_id in candidate_skills]
        gaps = [name for skill_id, name in required_skills.items() if skill_id not in candidate_skills]
        score = round(100 * len(matched_required) / max(len(required_skills), 1))
        matched_preview = ", ".join(matched_required[:3]) or "no required skill matches yet"
        recommendations.append(
            {
                "role": record["role"],
                "title": record["title"],
                "company": record["company"],
                "location": record["location"],
                "score": score,
                "matched_required_count": len(matched_required),
                "required_skill_count": len(required_skills),
                "matched_skills": matched_required,
                "preferred_matches": matched_preferred,
                "priority_gaps": gaps,
                "why": f"Your resume names {len(matched_required)} of {len(required_skills)} required skills in this role profile, including {matched_preview}.",
            }
        )

    recommendations.sort(
        key=lambda item: (
            -item["score"],
            -len(item["preferred_matches"]),
            item["title"].casefold(),
        )
    )
    recognized_skills = sorted(candidate_skills.values(), key=str.casefold)
    return {
        "recognized_skills": recognized_skills,
        "recommendations": recommendations,
        "basis": "Matches are based on recognized skill mentions compared with the required skills in 18 bundled role profiles. They are a starting point for exploration, not a hiring or career guarantee.",
    }


@app.post("/guide/recommendations")
async def guide_recommendations(payload: GuideRequest) -> dict[str, Any]:
    if not payload.profile_text.strip():
        raise HTTPException(422, "Add resume text or upload a resume to continue.")
    return await asyncio.to_thread(_career_recommendations, payload.profile_text)


@app.post("/guide/recommendations/upload")
async def guide_recommendations_upload(resume_file: Annotated[UploadFile, File()]) -> dict[str, Any]:
    extension = Path(resume_file.filename or "").suffix.lower()
    kinds = {".pdf": "pdf", ".docx": "docx", ".txt": "text", ".md": "text"}
    kind = kinds.get(extension)
    if not kind:
        raise HTTPException(415, "Upload a PDF, DOCX, TXT, or MD resume.")
    chunks: list[bytes] = []
    total_size = 0
    while chunk := await resume_file.read(1024 * 1024):
        total_size += len(chunk)
        if total_size > 20 * 1024 * 1024:
            raise HTTPException(413, "Resume uploads must be 20 MB or smaller.")
        chunks.append(chunk)
    content = b"".join(chunks)
    try:
        profile_text = parse_document(content, kind)["text"]
    except ValueError as exc:
        raise HTTPException(422, f"Could not read the resume: {exc}") from exc
    if not profile_text.strip():
        raise HTTPException(422, "No selectable text was found. Paste the resume text or upload a text-based PDF/DOCX.")
    if len(profile_text) > 200_000:
        raise HTTPException(413, "Extracted resume text is too long. Paste a focused resume under 200,000 characters.")
    return await asyncio.to_thread(_career_recommendations, profile_text)


def _account_response(user: dict[str, str], status_code: int = 200) -> JSONResponse:
    result = JSONResponse({"user": user}, status_code=status_code)
    result.set_cookie(
        "placementgap_session",
        _encode_session(user),
        max_age=60 * 60 * 24 * 7,
        httponly=True,
        secure=os.getenv("PLACEMENTGAP_HTTPS", "false").lower() == "true",
        samesite="lax",
        path="/",
    )
    return result


def _user_payload(row: sqlite3.Row) -> dict[str, str]:
    return {"sub": str(row["user_id"]), "email": str(row["email"]), "name": str(row["name"])}


def _password_digest(password: str, salt: bytes) -> bytes:
    return hashlib.scrypt(password.encode("utf-8"), salt=salt, n=2**14, r=8, p=1, dklen=32)


@app.post("/auth/register", status_code=201)
async def register_account(body: RegisterRequest) -> JSONResponse:
    email = body.email.strip().casefold()
    name = body.name.strip()
    if not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", email):
        raise HTTPException(422, "Enter a valid email address.")
    if not name:
        raise HTTPException(422, "Enter your name.")
    salt = secrets.token_bytes(16)
    digest = _password_digest(body.password, salt)
    try:
        with db() as conn:
            cursor = conn.execute(
                "INSERT INTO users(email,name,password_salt,password_hash,created) VALUES(?,?,?,?,?)",
                (email, name, salt.hex(), digest.hex(), time.time()),
            )
            row = conn.execute("SELECT * FROM users WHERE user_id=?", (cursor.lastrowid,)).fetchone()
    except sqlite3.IntegrityError as exc:
        raise HTTPException(409, "An account with this email already exists. Sign in instead.") from exc
    if row is None:
        raise HTTPException(500, "Could not create your account.")
    return _account_response(_user_payload(row), status_code=201)


@app.post("/auth/login")
async def login_account(body: LoginRequest) -> JSONResponse:
    email = body.email.strip().casefold()
    with db() as conn:
        row = conn.execute("SELECT * FROM users WHERE email=?", (email,)).fetchone()
    salt = bytes.fromhex(row["password_salt"]) if row else bytes(16)
    expected = bytes.fromhex(row["password_hash"]) if row else bytes(32)
    supplied = _password_digest(body.password, salt)
    if row is None or not hmac.compare_digest(supplied, expected):
        raise HTTPException(401, "Email or password is incorrect.")
    return _account_response(_user_payload(row))


@app.get("/auth/session")
async def auth_session(request: Request) -> dict[str, Any]:
    user = _decode_session(request.cookies.get("placementgap_session"))
    return {"user": user}


@app.post("/auth/logout")
async def auth_logout() -> JSONResponse:
    result = JSONResponse({"ok": True})
    result.delete_cookie("placementgap_session", path="/")
    return result


@app.middleware("http")
async def serve_frontend_and_rewrite_api(request: Request, call_next):  # type: ignore[no-untyped-def]
    path = request.url.path
    if path == "/api" or path.startswith("/api/"):
        rewritten_path = path[4:] or "/"
        request.scope["path"] = rewritten_path
        request.scope["raw_path"] = rewritten_path.encode("utf-8")
        request.__dict__.pop("_url", None)
        return await call_next(request)

    static_root = ROOT / "web" / "dist"
    index_file = static_root / "index.html"
    if index_file.is_file() and request.method in {"GET", "HEAD"}:
        candidate = (static_root / path.lstrip("/")).resolve()
        resolved_root = static_root.resolve()
        if candidate.is_relative_to(resolved_root) and candidate.is_file():
            return FileResponse(candidate)
        if "text/html" in request.headers.get("accept", ""):
            return FileResponse(index_file)

    return await call_next(request)
