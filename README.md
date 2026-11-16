# PlacementGap

**Explore engineering careers, understand your skill gaps, and build a practical plan to get placement-ready.**

PlacementGap is a career-planning website for engineering students. It brings career exploration, resume-based role suggestions, skill-gap analysis, and learning roadmaps into one workspace.

🌐 **Live site:** [placementgap.onrender.com](https://placementgap.onrender.com/)

## What you can do

- **Explore engineering roles:** browse 18 career paths in each of six disciplines: Computer Science & IT, Electronics & Communication, Electrical, Mechanical, Civil, and Chemical Engineering.
- **Open a role roadmap:** see a staged learning path, skills to build, a portfolio project, and related course recommendations.
- **Get personalized suggestions:** upload a resume in **Guide Me** to find career options that fit your experience and skills.
- **Analyze a skill gap:** compare your resume with a chosen role and review matching skills, missing skills, and actionable next steps.
- **Choose your appearance:** switch between light and dark themes.
- **Sign in:** create an account with email and password, or use Google or GitHub when those providers are configured.

## Technology

| Area | Tools |
| --- | --- |
| User interface | React, TypeScript, Vite, Lucide |
| API | Python, FastAPI, Uvicorn, Pydantic |
| Career analysis | Python role and skill profiles, deterministic matching and planning, optional LiteLLM extraction |
| Resume files | PDF and DOCX parsing, plus text input |
| Data | SQLite for local app data; PostgreSQL/pgvector services are included in the general Docker Compose setup |
| Authentication | Email/password sessions, Google Identity Services, GitHub OAuth; Resend for verification and security email |
| Browser testing and CI | Selenium, Docker Compose, Jenkins Pipeline |
| Hosting | Render using the included `render.yaml` and `Dockerfile` |

## Run locally

### Prerequisites

- Python 3.11 or newer
- Node.js 22 and Corepack (which provides pnpm)

From the repository root, install the dependencies:

```powershell
Set-Location "Placement Gap"
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
corepack enable
pnpm --dir web install
```

If your Python launcher does not have Python 3.12, replace `py -3.12` with `py -3.11` or `python` for a supported installed version.

Start the API in one terminal:

```powershell
Set-Location "Placement Gap"
.\.venv\Scripts\Activate.ps1
python -m uvicorn api.main:app --host 127.0.0.1 --port 8000 --reload
```

Start the website in a second terminal from the repository root:

```powershell
pnpm --dir "Placement Gap/web" dev
```

Open [http://localhost:5173](http://localhost:5173). The API docs are available at [http://localhost:8000/docs](http://localhost:8000/docs).

## Authentication and environment variables

Copy `Placement Gap/.env.example` to `Placement Gap/.env` and set only the credentials for sign-in methods or email features you want to enable. The app can use email/password, Google, and GitHub sign-in; email verification and security notifications require a Resend API key and a sender address verified with Resend.

Configure credentials on the **server** (for example, in Render's Environment settings). Never commit `.env` files, API keys, OAuth client secrets, or session secrets. Google uses `PLACEMENTGAP_GOOGLE_CLIENT_ID`; GitHub uses `PLACEMENTGAP_GITHUB_CLIENT_ID` and `PLACEMENTGAP_GITHUB_CLIENT_SECRET`; email delivery uses `PLACEMENTGAP_RESEND_API_KEY` and `PLACEMENTGAP_MAIL_FROM`. See the [detailed project README](<Placement Gap/README.md>) for provider setup and callback URLs.

## Checks and browser tests

Run the backend tests and lint from `Placement Gap` with the virtual environment active:

```powershell
python -m pytest -q tests
ruff check agent api ontology tests e2e
pnpm --dir web build
```

To run the full browser suite in an isolated Docker Compose stack:

```powershell
Set-Location "Placement Gap"
docker compose -f docker-compose.ci.yml up --build --abort-on-container-exit --exit-code-from e2e e2e
docker compose -f docker-compose.ci.yml down --volumes --remove-orphans
```

The browser tests cover sign-in with a disposable test user, theme switching, role exploration, resume recommendations, and skill-gap analysis. They do not use live OAuth credentials or send real email. Test results and failure screenshots are written under `Placement Gap/artifacts/selenium/`.

The repository-root `Jenkinsfile` runs lint, backend tests, and Selenium browser tests in Jenkins. See the [Jenkins and Selenium guide](<Placement Gap/JENKINS-SELENIUM.md>) for job setup.

## Deploy to Render

The included `render.yaml` configures the Render web service and health check. Connect the GitHub repository to Render and deploy the `main` branch. If automatic deploys are enabled, new pushes to that branch trigger a redeploy. Configure any required email and OAuth values in Render's environment settings, not in the repository.

The default SQLite data directory may not provide durable storage across service restarts or redeploys. Use a persistent disk or managed database before relying on the hosted service for long-term account and analysis storage.

## Repository layout

```text
.
├── Jenkinsfile                 # Jenkins CI pipeline
├── README.md                   # GitHub project overview
└── Placement Gap/
    ├── api/                    # FastAPI application
    ├── web/                    # React + TypeScript website
    ├── agent/ ontology/        # Analysis and career/skill data
    ├── tests/ e2e/             # Backend and Selenium tests
    ├── Dockerfile              # Production image
    ├── docker-compose.ci.yml   # Isolated browser-test stack
    └── render.yaml             # Render deployment settings
```
