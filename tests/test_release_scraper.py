from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from src.release_scraper import (
    build_artifact_manifest,
    load_fixture,
    normalize_date,
    parse_releases,
    write_outputs,
)

ROOT = Path(__file__).resolve().parents[1]


class ReleaseScraperTests(unittest.TestCase):
    def setUp(self) -> None:
        self.html = load_fixture(ROOT / "data" / "python_releases_fixture.html")

    def test_parse_releases_from_fixture(self) -> None:
        releases = parse_releases(self.html)
        self.assertGreaterEqual(len(releases), 6)
        self.assertEqual("3.13.5", releases[0].version)
        self.assertTrue(releases[0].detail_url.startswith("https://www.python.org/"))

    def test_normalize_date_returns_iso(self) -> None:
        self.assertEqual("2026-06-11", normalize_date("June 11, 2026"))

    def test_write_outputs_json_and_csv(self) -> None:
        releases = parse_releases(self.html, limit=4)
        with tempfile.TemporaryDirectory() as directory:
            out = Path(directory)
            json_path, csv_path = write_outputs(releases, out, source="test-fixture")
            self.assertTrue(json_path.is_file())
            self.assertTrue(csv_path.is_file())
            document = json.loads(json_path.read_text(encoding="utf-8"))
            self.assertEqual("HW25A066", document["metadata"]["student_id"])
            self.assertEqual(4, len(document["releases"]))

    def test_cli_offline_generates_outputs(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            subprocess.run(
                [sys.executable, str(ROOT / "scrape_releases.py"), "--offline", "--output-dir", directory],
                cwd=ROOT,
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            self.assertTrue((Path(directory) / "releases.json").is_file())
            self.assertTrue((Path(directory) / "releases.csv").is_file())

    def test_dashboard_script_generates_searchable_html(self) -> None:
        releases = parse_releases(self.html, limit=4)
        with tempfile.TemporaryDirectory() as directory:
            out = Path(directory)
            json_path, _ = write_outputs(releases, out, source="test-fixture")
            html_path = out / "index.html"
            subprocess.run(
                ["node", str(ROOT / "tools" / "generate_dashboard.js"), str(json_path), str(html_path)],
                cwd=ROOT,
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            html = html_path.read_text(encoding="utf-8")
            self.assertIn("Python Releases Dashboard", html)
            self.assertIn("search", html)
            self.assertIn("sort", html)

    def test_verify_outputs_writes_summary_and_manifest(self) -> None:
        releases = parse_releases(self.html, limit=4)
        with tempfile.TemporaryDirectory() as directory:
            out = Path(directory)
            json_path, _ = write_outputs(releases, out, source="test-fixture")
            html_path = out / "index.html"
            subprocess.run(
                ["node", str(ROOT / "tools" / "generate_dashboard.js"), str(json_path), str(html_path)],
                cwd=ROOT,
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            subprocess.run(
                [sys.executable, str(ROOT / "tools" / "verify_outputs.py"), str(out)],
                cwd=ROOT,
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            self.assertTrue((out / "build_summary.json").is_file())
            self.assertTrue((out / "artifact_manifest.json").is_file())

    def test_artifact_manifest_contains_sha256(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            out = Path(directory)
            path = out / "sample.txt"
            path.write_text("release-manifest-test", encoding="utf-8")
            manifest = build_artifact_manifest(out, [path])
            self.assertEqual(64, len(manifest["artifacts"][0]["sha256"]))


if __name__ == "__main__":
    unittest.main()

