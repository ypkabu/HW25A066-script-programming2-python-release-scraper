from __future__ import annotations

import argparse
import sys
from pathlib import Path

from src.release_scraper import PYTHON_RELEASES_URL, fetch_html, load_fixture, parse_releases, write_outputs


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Python公式サイトのリリース情報を取得します。")
    parser.add_argument("--output-dir", type=Path, default=Path("output"))
    parser.add_argument("--fixture", type=Path, default=Path("data/python_releases_fixture.html"))
    parser.add_argument("--offline", action="store_true", help="python.orgへ接続せずfixtureを使用")
    parser.add_argument("--no-fallback", action="store_true", help="ネットワーク失敗時にfixtureへ切り替えない")
    parser.add_argument("--limit", type=int, default=12)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.offline:
        print(f"[scrape] offline mode: {args.fixture}")
        html = load_fixture(args.fixture)
        source = f"fixture:{args.fixture.as_posix()}"
    else:
        try:
            print("[scrape] requesting python.org downloads page")
            html = fetch_html()
            source = PYTHON_RELEASES_URL
            print("[scrape] live request succeeded")
        except Exception as exc:
            if args.no_fallback:
                print(f"[scrape] request failed: {exc}", file=sys.stderr)
                return 1
            print(f"[scrape] request failed; use fixture instead: {exc}")
            html = load_fixture(args.fixture)
            source = f"fixture-fallback:{args.fixture.as_posix()}"

    releases = parse_releases(html, limit=args.limit)
    if not releases:
        print("[scrape] no Python releases were parsed", file=sys.stderr)
        return 1
    json_path, csv_path = write_outputs(releases, args.output_dir, source=source)
    print(f"[scrape] generated {len(releases)} releases")
    print(f"[scrape] JSON: {json_path}")
    print(f"[scrape] CSV : {csv_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
