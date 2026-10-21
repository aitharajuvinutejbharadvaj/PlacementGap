from __future__ import annotations

from urllib.parse import quote_plus

OFFICIAL: dict[str, tuple[str, str]] = {
    "python": ("Python tutorial", "https://docs.python.org/3/tutorial/"),
    "javascript": (
        "MDN JavaScript guide",
        "https://developer.mozilla.org/en-US/docs/Web/JavaScript/Guide",
    ),
    "typescript": (
        "TypeScript handbook",
        "https://www.typescriptlang.org/docs/handbook/intro.html",
    ),
    "react": ("React documentation", "https://react.dev/learn"),
    "nextjs": ("Next.js documentation", "https://nextjs.org/docs"),
    "docker": ("Docker getting started", "https://docs.docker.com/get-started/"),
    "kubernetes": ("Kubernetes tutorials", "https://kubernetes.io/docs/tutorials/"),
    "git": ("Pro Git book", "https://git-scm.com/book/en/v2"),
    "sql": ("PostgreSQL tutorial", "https://www.postgresql.org/docs/current/tutorial.html"),
    "postgresql": ("PostgreSQL tutorial", "https://www.postgresql.org/docs/current/tutorial.html"),
    "machine_learning": (
        "Google Machine Learning Crash Course",
        "https://developers.google.com/machine-learning/crash-course",
    ),
    "pytorch": ("PyTorch tutorials", "https://pytorch.org/tutorials/"),
    "tensorflow": ("TensorFlow tutorials", "https://www.tensorflow.org/tutorials"),
    "pandas": (
        "Pandas getting started",
        "https://pandas.pydata.org/docs/getting_started/index.html",
    ),
    "fastapi": ("FastAPI tutorial", "https://fastapi.tiangolo.com/tutorial/"),
    "linux": (
        "Linux command line basics",
        "https://ubuntu.com/tutorials/command-line-for-beginners",
    ),
    "html": (
        "MDN HTML guide",
        "https://developer.mozilla.org/en-US/docs/Learn_web_development/Core/Structuring_content",
    ),
    "css": (
        "MDN CSS guide",
        "https://developer.mozilla.org/en-US/docs/Learn_web_development/Core/Styling_basics",
    ),
}


def find_resources(
    skill_id: str, from_level: str, to_level: str, budget: float, max_n: int = 5
) -> list[dict[str, str]]:
    if budget <= 0 or max_n <= 0:
        return []
    title, url = OFFICIAL.get(
        skill_id,
        (
            f"{skill_id.replace('_', ' ')} learning resources",
            f"https://www.google.com/search?q={quote_plus(skill_id.replace('_', ' '))}+official+documentation",
        ),
    )
    return [{"title": title, "url": url, "cost": "free"}]
