#!/usr/bin/env python3
"""
EDB Circular Vault — notify pipeline (Pages-first).

  summarize → pages_build → (optional) telegram

Usage:
  python3 notify_pipeline.py --dry-run --limit 2
  python3 notify_pipeline.py --limit 10 --skip-telegram
  python3 notify_pipeline.py --ids EDBCM26149 --skip-pages
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DEFAULT_PAGES_OUT = Path("/workspace/github-apply/edb-circular-vault/docs/data")
DEFAULT_CSV = Path("/workspace/github-apply/edb-circular-vault/data/circulars.csv")


def run(script: str, extra: list[str]) -> int:
    cmd = [sys.executable, str(ROOT / script), *extra]
    print(f"\n>>> {' '.join(cmd)}", flush=True)
    return subprocess.call(cmd, cwd=str(ROOT))


def main() -> int:
    parser = argparse.ArgumentParser(
        description="EDB pipeline: summarize → pages_build → telegram"
    )
    parser.add_argument("--dry-run", action="store_true", help="No LLM API / no Telegram send")
    parser.add_argument("--limit", type=int, default=0, help="Max circulars")
    parser.add_argument("--ids", default="", help="Comma-separated circular ids")
    parser.add_argument("--force", action="store_true", help="Overwrite existing summaries")
    parser.add_argument("--from-metadata", action="store_true", help="Use metadata/ if queue empty")
    parser.add_argument("--skip-summarize", action="store_true", help="Skip LLM summarize")
    parser.add_argument("--skip-pages", action="store_true", help="Skip GitHub Pages data build")
    parser.add_argument(
        "--skip-telegram",
        "--skip-notify",
        dest="skip_telegram",
        action="store_true",
        help="Skip Telegram (default for Pages-first; Telegram is optional)",
    )
    parser.add_argument(
        "--with-telegram",
        action="store_true",
        help="Also run telegram_notify after pages_build",
    )
    parser.add_argument(
        "--pages-out",
        default=str(DEFAULT_PAGES_OUT),
        help="Output dir for summaries.json",
    )
    args = parser.parse_args()

    # Pages-first: telegram off unless --with-telegram
    do_telegram = args.with_telegram and not args.skip_telegram

    common: list[str] = []
    if args.dry_run:
        common.append("--dry-run")
    if args.limit and args.limit > 0:
        common.extend(["--limit", str(args.limit)])
    if args.ids.strip():
        common.extend(["--ids", args.ids.strip()])

    rc = 0
    if not args.skip_summarize:
        sum_args = list(common)
        if args.force:
            sum_args.append("--force")
        if args.from_metadata:
            sum_args.append("--from-metadata")
        rc = run("llm_summarize.py", sum_args)
        if rc != 0:
            print(f"WARN: summarize exited {rc}; continuing", flush=True)

    if not args.skip_pages:
        pages_args = [
            "--out",
            args.pages_out,
            "--write-individual",
        ]
        if DEFAULT_CSV.is_file():
            pages_args.extend(["--csv", str(DEFAULT_CSV)])
        prc = run("pages_build.py", pages_args)
        if prc != 0:
            rc = prc

    if do_telegram:
        notify_args = list(common)
        if args.dry_run:
            notify_args.append("--skip-ia-check")
        nrc = run("telegram_notify.py", notify_args)
        if nrc != 0:
            rc = nrc
    else:
        print("\n(skip telegram — Pages-first; pass --with-telegram to enable)", flush=True)

    print(f"\n=== notify_pipeline finished rc={rc} ===", flush=True)
    return rc


if __name__ == "__main__":
    sys.exit(main())
