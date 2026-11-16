from __future__ import annotations

from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.select import Select
from selenium.webdriver.support.ui import WebDriverWait


def click_when_visible(driver, locator, timeout=20):
    wait = WebDriverWait(driver, timeout)
    element = wait.until(EC.element_to_be_clickable(locator))
    driver.execute_script(
        "arguments[0].scrollIntoView({block: 'center', inline: 'nearest'});",
        element,
    )
    wait.until(EC.element_to_be_clickable(locator)).click()


def test_role_explorer_branch_filter_and_roadmap(signed_in):
    driver = signed_in
    wait = WebDriverWait(driver, 30)

    branch_filter = wait.until(
        EC.presence_of_element_located((By.CSS_SELECTOR, ".catalog-branch-select select"))
    )
    Select(branch_filter).select_by_value("Mechanical Engineering")
    wait.until(
        lambda browser: browser.find_element(By.CSS_SELECTOR, ".catalog-filter-count").text
        == "18 career paths"
    )

    click_when_visible(driver, (By.CSS_SELECTOR, ".catalog-card"))
    roadmap = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, '[role="dialog"]')))
    assert "Mechanical Engineering" in roadmap.text
    assert "Courses" in roadmap.text
    driver.find_element(By.CSS_SELECTOR, '[aria-label="Close role roadmap"]').click()


def test_guide_me_recommends_roles_from_resume_skills(signed_in):
    driver = signed_in
    wait = WebDriverWait(driver, 30)
    guide = wait.until(EC.presence_of_element_located((By.ID, "guide-me")))
    driver.execute_script(
        "arguments[0].scrollIntoView({block: 'center'});", guide
    )

    branch_filter = driver.find_element(By.CSS_SELECTOR, ".guide-branch-field select")
    Select(branch_filter).select_by_visible_text("Computer Science & IT")
    driver.find_element(By.ID, "guide-resume-text").send_keys(
        "Built a Python API using SQL, PostgreSQL, Git, Linux, Docker, and React. "
        "Developed database queries and deployed the project in containers."
    )
    click_when_visible(driver, (By.CSS_SELECTOR, ".guide-submit"))

    results = wait.until(EC.visibility_of_element_located((By.ID, "guide-results")))
    wait.until(lambda browser: len(browser.find_elements(By.CSS_SELECTOR, ".guide-match-card")) > 0)
    assert "Python" in results.text
    assert "roles compared" in results.text
    assert len(driver.find_elements(By.CSS_SELECTOR, ".guide-match-card")) == 5


def test_skill_gap_review_and_report_approval(signed_in):
    driver = signed_in
    wait = WebDriverWait(driver, 45)

    intake = wait.until(EC.presence_of_element_located((By.ID, "intake-panel")))
    driver.execute_script(
        "arguments[0].scrollIntoView({block: 'center'});", intake
    )
    driver.find_element(By.CSS_SELECTOR, ".tab-content textarea.record-input").send_keys(
        "Built and deployed a Python service. Used SQL, Git, and Docker in a student project."
    )
    click_when_visible(driver, (By.XPATH, "//button[contains(., 'Target role')]"))
    click_when_visible(driver, (By.XPATH, "//button[contains(., 'Paste JD')]"))
    job_description = driver.find_element(By.CSS_SELECTOR, ".tab-content textarea.record-input")
    job_description.send_keys(
        "Required skills: Python, SQL, Docker, Linux, cloud computing, and Kubernetes."
    )
    click_when_visible(driver, (By.CSS_SELECTOR, ".primary-button"))

    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".analysis-gap-card")))
    approval = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, ".approval")))
    assert "Review before report" in approval.text
    click_when_visible(driver, (By.CSS_SELECTOR, ".approve-button"))
    wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, ".download-row")))
    report_links = driver.find_elements(By.CSS_SELECTOR, ".download-row a")
    assert {link.text for link in report_links} >= {"Markdown", "PDF", "JSON"}


def test_theme_toggle_switches_workspace_mode(signed_in):
    driver = signed_in
    wait = WebDriverWait(driver, 15)
    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".app-shell")))
    driver.find_element(By.CSS_SELECTOR, ".workspace-theme-toggle").click()
    wait.until(
        lambda browser: "theme-dark"
        in browser.find_element(By.CSS_SELECTOR, ".app-shell").get_attribute("class")
    )
    assert "theme-dark" in driver.find_element(By.CSS_SELECTOR, ".app-shell").get_attribute("class")
