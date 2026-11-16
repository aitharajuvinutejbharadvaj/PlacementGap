# Jenkins, Docker, and Selenium CI

The repository root contains a `Jenkinsfile`. It builds the production app image, runs Python lint and API tests, then starts an isolated app plus Selenium Chrome container and drives the browser through the core user journeys. Jenkins publishes JUnit XML and failure screenshots.

## What is required on the Jenkins agent

- Jenkins with Pipeline and JUnit plugins.
- A Docker-capable agent with Docker Engine and the Docker Compose v2 plugin. The pipeline supports Unix shell and Windows batch agents; Linux containers must be enabled in Docker Desktop on Windows.
- Git access to the `PlacementGap` repository.

The CI run does not need Google/GitHub OAuth credentials or a Resend key. It seeds a verified test user in an isolated disposable SQLite volume. The app runs in fixture mode; tests do not access the live Render service or send real emails.

## Create the Jenkins job

1. In Jenkins, create **New Item → Pipeline**.
2. Under **Pipeline**, choose **Pipeline script from SCM**, select Git, and enter the PlacementGap GitHub repository URL and branch `main`.
3. Keep the script path as `Jenkinsfile` (it is at the repository root), save, and select **Build Now**.
4. Open the build’s **Test Result** page for test totals. Failure screenshots and JUnit XML are archived as build artifacts.

The Jenkins agent, rather than the Jenkins controller, must be able to run Docker commands. On Windows, ensure Jenkins runs under a user that can access Docker Desktop and its Linux container engine.

## Run the checks locally with Docker

From the `Placement Gap` project folder:

```powershell
docker compose -f docker-compose.ci.yml up --build --abort-on-container-exit --exit-code-from e2e e2e
docker compose -f docker-compose.ci.yml down --volumes --remove-orphans
```

The first command builds the app and test runner, starts the app and Selenium Chrome, seeds the disposable test account, and runs the UI tests. The second removes the test containers and their temporary database. Results and failure screenshots are written under `artifacts/selenium/`.

To run the Selenium suite against a local API instead, install the development dependencies and Chrome, then use two terminals from the project folder. Use the same data directory and session secret in both terminals so the test runner seeds the database the API is using:

```powershell
$env:PLACEMENTGAP_DATA_DIR = (Join-Path $PWD "outputs/selenium-ci")
$env:PLACEMENTGAP_SESSION_SECRET = "local-selenium-only-secret"
$env:PLACEMENTGAP_HTTPS = "false"
python -m uvicorn api.main:app --host 127.0.0.1 --port 8001
```

In the second terminal:

```powershell
$env:PLACEMENTGAP_DATA_DIR = (Join-Path $PWD "outputs/selenium-ci")
$env:PLACEMENTGAP_SESSION_SECRET = "local-selenium-only-secret"
$env:PLACEMENTGAP_HTTPS = "false"
$env:PLACEMENTGAP_BASE_URL = "http://127.0.0.1:8001"
python -m pytest -q e2e --junitxml=artifacts/selenium/junit.xml
```

## Browser journeys covered

- Sign in using a test-only verified account.
- Switch the workspace theme.
- Filter the Role Explorer by engineering branch and open a roadmap.
- Submit resume text to Guide Me and verify role matches render.
- Run a skill-gap analysis, review and approve its plan, and verify report links appear.
