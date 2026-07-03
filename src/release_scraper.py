from __future__ import annotations

import csv
import hashlib
import html.parser
import json
import os
import re
import urllib.parse
import urllib.request
from dataclasses import asdict, dataclass
from datetime import datetime
from email.utils import parsedate_to_datetime
from pathlib import Path
from typing import Any, Iterable

PYTHON_RELEASES_URL = "https://www.python.org/downloads/source/"
PYTHON_BASE_URL = "https://www.python.org"


@dataclass(frozen=True)
class PythonRelease:
    version: str
    published_date: str
    detail_url: str


class PythonReleaseParser(html.parser.HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.releases: list[PythonRelease] = []
        self._current_href: str | None = None
        self._current_version: str | None = None
        self._capture_date = False
        self._date_parts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attrs_dict = {key: value or "" for key, value in attrs}
        classes = attrs_dict.get("class", "")
        if tag == "a":
            href = attrs_dict.get("href", "")
            if "/downloads/release/python-" in href:
                self._current_href = href
        if tag in {"span", "time"} and "release-date" in classes:
            self._capture_date = True
            self._date_parts = []

    def handle_data(self, data: str) -> None:
        text = " ".join(data.split())
        if not text:
            return
        if self._current_href and self._current_version is None:
            inline = re.search(
                r"Python\s+(\d+\.\d+\.\d+(?:[a-z]\d+)?)\s*-\s*([A-Za-z]+\s+\d{1,2},?\s+\d{4})",
                text,
                re.I,
            )
            if inline:
                self._current_version = inline.group(1)
                self._date_parts = [inline.group(2)]
                self._maybe_add_release()
                return
            match = re.search(r"Python\s+(\d+\.\d+\.\d+(?:[a-z]\d+)?)", text, re.I)
            if match:
                self._current_version = match.group(1)
        if self._capture_date:
            self._date_parts.append(text)

    def handle_endtag(self, tag: str) -> None:
        if tag in {"span", "time"} and self._capture_date:
            self._capture_date = False
            self._maybe_add_release()
        if tag in {"li", "article"}:
            self._reset_current()

    def _maybe_add_release(self) -> None:
        if not self._current_href or not self._current_version or not self._date_parts:
            return
        published_date = normalize_date(" ".join(self._date_parts))
        detail_url = urllib.parse.urljoin(PYTHON_BASE_URL, self._current_href)
        release = PythonRelease(self._current_version, published_date, detail_url)
        if release not in self.releases:
            self.releases.append(release)

    def _reset_current(self) -> None:
        self._current_href = None
        self._current_version = None
        self._capture_date = False
        self._date_parts = []


def normalize_date(value: str) -> str:
    clean = " ".join(value.replace(",", " ").split())
    for fmt, candidate in [
        ("%B %d, %Y", value),
        ("%B %d %Y", clean),
        ("%b %d, %Y", value),
        ("%b %d %Y", clean),
    ]:
        try:
            return datetime.strptime(candidate, fmt).date().isoformat()
        except ValueError:
            pass
    for candidate in (value, clean):
        try:
            return parsedate_to_datetime(candidate).date().isoformat()
        except (TypeError, ValueError, IndexError):
            pass
    return value.strip()


def fetch_html(url: str = PYTHON_RELEASES_URL, timeout_seconds: int = 20) -> str:
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "HW25A066-python-release-scraper/1.0",
            "Accept": "text/html,application/xhtml+xml",
            "Accept-Encoding": "identity",
        },
    )
    with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
        if response.status != 200:
            raise RuntimeError(f"python.org returned HTTP {response.status}")
        return response.read().decode("utf-8", errors="replace")


def load_fixture(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def parse_releases(html: str, limit: int = 12) -> list[PythonRelease]:
    parser = PythonReleaseParser()
    parser.feed(html)
    releases = parser.releases
    if not releases:
        releases = parse_releases_with_regex(html)
    unique: dict[tuple[str, str], PythonRelease] = {}
    for item in releases:
        unique[(item.version, item.detail_url)] = item
    return list(unique.values())[:limit]


def parse_releases_with_regex(html: str) -> list[PythonRelease]:
    inline_pattern = re.compile(
        r'href="(?P<href>/downloads/release/python-[^"]+)">(?:Latest Python 3 Release - )?Python\s+'
        r'(?P<version>\d+\.\d+\.\d+(?:[a-z]\d+)?)\s*-\s*(?P<date>[A-Za-z]+\s+\d{1,2},?\s+\d{4})</a>',
        re.I | re.S,
    )
    releases = [
        PythonRelease(
            version=match.group("version"),
            published_date=normalize_date(match.group("date")),
            detail_url=urllib.parse.urljoin(PYTHON_BASE_URL, match.group("href")),
        )
        for match in inline_pattern.finditer(html)
    ]
    if releases:
        return releases

    legacy_pattern = re.compile(
        r'href="(?P<href>/downloads/release/python-[^"]+)">Python\s+(?P<version>\d+\.\d+\.\d+(?:[a-z]\d+)?)</a>.*?'
        r'(?:release-date[^>]*>|<time[^>]*>)(?P<date>[A-Za-z]+\s+\d{1,2},?\s+\d{4})',
        re.I | re.S,
    )
    for match in legacy_pattern.finditer(html):
        releases.append(
            PythonRelease(
                version=match.group("version"),
                published_date=normalize_date(match.group("date")),
                detail_url=urllib.parse.urljoin(PYTHON_BASE_URL, match.group("href")),
            )
        )
    return releases


def write_outputs(
    releases: list[PythonRelease],
    output_dir: Path,
    *,
    source: str,
) -> tuple[Path, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    generated_at = datetime.now().astimezone().isoformat(timespec="seconds")
    json_path = output_dir / "releases.json"
    csv_path = output_dir / "releases.csv"
    document = {
        "metadata": {
            "student_id": "HW25A066",
            "student_name": "嶋田一歩",
            "source": source,
            "generated_at": generated_at,
            "count": len(releases),
        },
        "releases": [asdict(item) for item in releases],
    }
    json_path.write_text(json.dumps(document, ensure_ascii=False, indent=2), encoding="utf-8")
    with csv_path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["version", "published_date", "detail_url"])
        writer.writeheader()
        for item in releases:
            writer.writerow(asdict(item))
    return json_path, csv_path


def build_artifact_manifest(output_dir: Path, artifact_paths: Iterable[Path]) -> dict[str, Any]:
    generated_at = datetime.now().astimezone().isoformat(timespec="seconds")
    build_number = os.environ.get("BUILD_NUMBER", "local")
    entries = []
    for path in sorted({Path(item) for item in artifact_paths}, key=lambda item: item.name):
        if not path.is_file():
            continue
        entries.append(
            {
                "file_name": path.name,
                "size": path.stat().st_size,
                "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                "generated_at": generated_at,
                "build_number": build_number,
            }
        )
    return {"artifacts": entries}
