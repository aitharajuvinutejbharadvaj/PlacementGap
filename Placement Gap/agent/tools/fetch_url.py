from __future__ import annotations

import hashlib
import ipaddress
import socket
import urllib.parse
import urllib.request
import urllib.robotparser
from email.message import Message
from html.parser import HTMLParser
from typing import Any
from urllib.error import HTTPError, URLError


class _VisibleText(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []
        self.hidden = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() in {"script", "style", "noscript", "template", "svg"}:
            self.hidden += 1

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() in {"script", "style", "noscript", "template", "svg"} and self.hidden:
            self.hidden -= 1

    def handle_data(self, data: str) -> None:
        if not self.hidden and data.strip():
            self.parts.append(data.strip())


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(
        self,
        req: urllib.request.Request,
        fp: Any,
        code: int,
        msg: str,
        headers: Message,
        newurl: str,
    ) -> urllib.request.Request | None:
        return None


def html_to_text(body: str) -> str:
    parser = _VisibleText()
    parser.feed(body)
    return " ".join(" ".join(parser.parts).split())


def fetch_url(url: str) -> dict[str, str]:
    if not url.startswith("https://"):
        raise ValueError("Only HTTPS sources are supported")
    parsed = urllib.parse.urlparse(url)
    if not parsed.hostname:
        raise ValueError("URL must include a hostname")
    if parsed.port not in (None, 443):
        raise ValueError("Only the standard HTTPS port is supported")
    opener = urllib.request.build_opener(_NoRedirect)
    for result in socket.getaddrinfo(parsed.hostname, 443, type=socket.SOCK_STREAM):
        ip = ipaddress.ip_address(result[4][0])
        if not ip.is_global:
            raise ValueError("Private or local network destinations are blocked")
    robots_url = f"https://{parsed.hostname}/robots.txt"
    robots = urllib.robotparser.RobotFileParser(robots_url)
    try:
        robots_request = urllib.request.Request(
            robots_url, headers={"User-Agent": "PlacementGap/0.1"}
        )
        with opener.open(robots_request, timeout=5) as response:
            robots.parse(response.read(256_000).decode("utf-8", "replace").splitlines())
    except HTTPError as exc:
        if exc.code != 404:
            raise ValueError(f"robots.txt request failed with HTTP {exc.code}") from exc
        robots.parse([])
    except URLError as exc:
        raise ValueError("Could not check robots.txt; refusing to fetch the job page") from exc
    if not robots.can_fetch("PlacementGap/0.1", url):
        raise ValueError("robots.txt does not permit this fetch")
    req = urllib.request.Request(url, headers={"User-Agent": "PlacementGap/0.1"})
    with opener.open(req, timeout=15) as response:
        content_type = response.headers.get("Content-Type", "")
        if any(x in content_type for x in ["application/pdf", "application/octet-stream"]):
            raise ValueError("URL returned a binary document; upload it instead")
        body_bytes = response.read(2_000_001)
        if len(body_bytes) > 2_000_000:
            raise ValueError("Job page exceeds the 2 MB fetch limit")
        body = body_bytes.decode("utf-8", "replace")
    body = html_to_text(body)
    return {"url": url, "content_hash": hashlib.sha256(body.encode()).hexdigest(), "text": body}
