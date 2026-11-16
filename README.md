# PlacementGap

**Explore engineering careers, understand your skill gaps, and build a practical plan to get placement-ready.**

PlacementGap is a career-planning website for engineering students. It brings career exploration, resume-based role suggestions, skill-gap analysis, and learning roadmaps into one workspace.

🌐 **Live Site:** [https://placementgap.onrender.com/](https://placementgap.onrender.com/)

## What You Can Do

- **Explore Engineering Roles:** Browse 18 career paths in each of six disciplines: Computer Science & IT, Electronics & Communication, Electrical, Mechanical, Civil, and Chemical Engineering.
- **Open a Role Roadmap:** Explore a staged learning path, skills to build, a portfolio project, and related course recommendations.
- **Get Personalized Suggestions:** Upload a resume in **Guide Me** to discover career options that match your experience and skills.
- **Analyze Your Skill Gap:** Compare your resume with a selected role and review matching skills, missing skills, and actionable next steps.
- **Choose Your Appearance:** Switch between light and dark themes.
- **Sign In Securely:** Create an account using email and password, or sign in through Google or GitHub when those providers are configured.

## Technology Stack

| Area | Tools |
|---|---|
| User Interface | React, TypeScript, Vite, Lucide |
| API | Python, FastAPI, Uvicorn, Pydantic |
| Career Analysis | Python role and skill profiles, deterministic matching and planning, optional LiteLLM extraction |
| Resume Processing | PDF and DOCX parsing, plus text input |
| Database | SQLite for local app data; PostgreSQL/pgvector services in the general Docker Compose setup |
| Authentication | Email/password sessions, Google Identity Services, GitHub OAuth |
| Email Services | Resend for verification and security notifications |
| Browser Testing & CI | Selenium, Docker Compose, Jenkins Pipeline |
| Hosting | Render using the included `render.yaml` and `Dockerfile` |

## Run Locally

### Prerequisites

- Python 3.11 or newer
- Node.js 22
- Corepack (included with Node.js and used to manage pnpm)

### Installation

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

### Start the Backend

Open a terminal and run:

```powershell
Set-Location "Placement Gap"
.\.venv\Scripts\Activate.ps1

python -m uvicorn api.main:app --host 127.0.0.1 --port 8000 --reload
```

### Start the Frontend

Open a second terminal from the repository root:

```powershell
pnpm --dir "Placement Gap/web" dev
```

### Access the Application

- Website: http://localhost:5173
- Backend