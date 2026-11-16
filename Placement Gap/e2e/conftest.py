from __future__ import annotations

import os
import secrets
import time
import urllib.error
import urllib.request
from collections.abc import Iterator
from pathlib import Path

import pytest
from selenium import webdriver
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.remote.webdriver import WebDriver

TEST_EMAIL = "placementgap.selenium@example.test"
TEST_PASSWORD = "Selenium-CI-test-password-2026"
ARTIFACTS = Path(
    os.getenv(
        "PLACEMENTGAP_ARTIFACTS",
        str(Path(__file__).resolve().parents[1] / "artifacts" / "selenium"),
    )
)


@pytest.fixture(scope="session", autouse=True)
def verified_test_account() -> Iterator[None]:
    """Seed a verified account in the disposable CI database; never call a real mail service."""
    from api import main as api

    salt = secrets.token_bytes(16)
    with api.db() as conn:
        conn.execute("DELETE FROM users WHERE email=?", (TEST_EMAIL,))
        conn.execute(
            "INSERT INTO users(email,name,password_salt,password_hash,created,email_verified) "
            "VALUES(?,?,?,?,?,1)",
            (
                TEST_EMAIL,
                "Selenium Test User",
                salt.hex(),
                api._password_digest(TEST_PASSWORD, salt).hex(),
                time.time(),
            ),
        )
    yield
    with api.db() as conn:
        conn.execute("DELETE FROM users WHERE email=?", (TEST_EMAIL,))


@pytest.fixture
def driver() -> Iterator[WebDriver]:
    options = ChromeOptions()
    options.add_argument("--headless=new")
    options.add_argument("--window-size=1440,1200")
    options.add_argument("--disable-dev-shm-usage")

    remote_url = os.getenv("SELENIUM_REMOTE_URL", "").strip()
    if remote_url:
        status_url = remote_url.split("/wd/hub", maxsplit=1)[0] + "/status"
        deadline = time.monotonic() + 90
        while True:
            try:
                with urllib.request.urlopen(status_url, timeout=3) as response:
                    if response.status == 200:
                        break
            except (OSError, urllib.error.URLError):
                pass
            if time.monotonic() >= deadline:
                raise RuntimeError(f"Selenium server did not become ready: {status_url}")
            time.sleep(2)
        browser = webdriver.Remote(command_executor=remote_url, options=options)
    else:
        # Selenium Manager resolves a matching local ChromeDriver for developer runs.
        browser = webdriver.Chrome(options=options)

    browser.set_page_load_timeout(60)
    try:
        yield browser
    finally:
        browser.quit()


@pytest.fixture
def signed_in(driver: WebDriver) -> WebDriver:
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.support.ui import WebDriverWait

    base_url = os.getenv("PLACEMENTGAP_BASE_URL", "http://127.0.0.1:8000").rstrip("/")
    driver.get(base_url)
    wait = WebDriverWait(driver, 30)
    wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, 'input[autocomplete="email"]')))
    driver.find_element(By.CSS_SELECTOR, 'input[autocomplete="email"]').send_keys(TEST_EMAIL)
    driver.find_element(By.CSS_SELECTOR, 'input[autocomplete="current-password"]').send_keys(
        TEST_PASSWORD
    )
    driver.find_element(By.CSS_SELECTOR, ".auth-submit").click()
    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".app-shell")))
    # The app animates anchor scrolling; disable that for deterministic browser automation.
    driver.execute_script("document.documentElement.style.scrollBehavior = 'auto';")
    return driver


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item: pytest.Item, call: pytest.CallInfo[None]):
    outcome = yield
    report = outcome.get_result()
    if report.when != "call" or not report.failed:
        return
    browser = item.funcargs.get("driver") or item.funcargs.get("signed_in")
    if browser is None:
        return
    ARTIFACTS.mkdir(parents=True, exist_ok=True)
    filename = item.name.replace("/", "_").replace(" ", "_")
    browser.save_screenshot(str(ARTIFACTS / f"{filename}.png"))
