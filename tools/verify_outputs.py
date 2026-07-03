from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.release_scraper import build_artifact_manifest


def main() -> int:
    output = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("output")
    required = [output / "releases.json", output / "releases.csv", output / "index.html"]
    missing = [str(path) for path in required if not path.is_file() or path.stat().st_size == 0]
    if missing:
        print("[verify] missing or empty outputs:", *missing, sep="\n- ", file=sys.stderr)
        return 1

    document = json.loads((output / "releases.json").read_text(encoding="utf-8"))
    releases = document.get("releases", [])
    if len(releases) < 3:
        print(f"[verify] too few releases: {len(releases)}", file=sys.stderr)
        return 1

    with (output / "releases.csv").open("r", encoding="utf-8-sig", newline="") as handle:
        csv_rows = list(csv.DictReader(handle))
    if len(csv_rows) != len(releases):
        print("[verify] JSON/CSV row counts differ", file=sys.stderr)
        return 1

    html = (output / "index.html").read_text(encoding="utf-8")
    for token in ["<!doctype html>", "Python Releases Dashboard", "releaseRows", "HW25A066"]:
        if token not in html:
            print(f"[verify] token not found in HTML: {token}", file=sys.stderr)
            return 1

    summary_path = output / "build_summary.json"
    summary = {
        "status": "SUCCESS",
        "release_rows": len(releases),
        "source": document.get("metadata", {}).get("source"),
        "files": {path.name: path.stat().st_size for path in required},
    }
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    manifest_path = output / "artifact_manifest.json"
    manifest_path.write_text(
        json.dumps(build_artifact_manifest(output, [*required, summary_path]), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"[verify] success: {len(releases)} releases, 5 artifacts")
    print(f"[verify] manifest: {manifest_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

