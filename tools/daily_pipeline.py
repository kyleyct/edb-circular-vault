#!/usr/bin/env python3
"""
EDB Circular Vault — twice-daily sync orchestrator (HKT morning + evening).

Always:
  1) edb_daily.py          — scrape / download new circulars
  2) ia_upload_run.py      — upload new PDFs to Internet Archive (skip if none)
  3) notify_pipeline.py    — summarize new + ALWAYS pages_build (bumps last_synced_at)
  4) optional: commit+push vault docs/data so GitHub Pages shows the sync time

Even when there are zero new circulars, step 3 still rewrites summaries.json
with a fresh last_synced_at so the website proves the sync ran.

Recommended Grok Bot / cron times (Asia/Hong_Kong):
  - Morning: 08:45 HKT
  - Evening: 18:45 HKT

Usage:
  python3 daily_pipeline.py
  python3 daily_pipeline.py --days 7 --skip-ia
  python3 daily_pipeline.py --push   # also git commit+push vault docs if changed
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
VAULT = Path("/workspace/github-apply/edb-circular-vault")
PAGES_OUT = VAULT / "docs" / "data"


def run(cmd: list[str], cwd: Path | None = None) -> int:
    print(f"\n>>> {' '.join(cmd)}", flush=True)
    return subprocess.call(cmd, cwd=str(cwd or ROOT))


def push_pages_if_changed() -> int:
    if not VAULT.is_dir() or not (VAULT / ".git").is_dir():
        print("WARN: vault repo not found; skip push", flush=True)
        return 0
    status = subprocess.check_output(
        ["git", "status", "--porcelain", "docs/"], cwd=str(VAULT), text=True
    ).strip()
    if not status:
        print("No docs/ changes to push (timestamp may be unchanged if build skipped).", flush=True)
        return 0
    cmds = [
        ["git", "add", "docs/"],
        [
            "git",
            "commit",
            "-m",
            "chore: twice-daily sync — bump last_synced_at (empty or with new circulars)\n\n"
            "Recommended cron (HKT): 08:45 and 18:45.",
        ],
        ["git", "push", "origin", "main"],
    ]
    for c in cmds:
        rc = run(c, cwd=VAULT)
        if rc != 0:
            return rc
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="EDB twice-daily sync pipeline")
    parser.add_argument("--days", type=int, default=7)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--skip-ia", action="store_true")
    parser.add_argument("--skip-summarize", action="store_true")
    parser.add_argument(
        "--push",
        action="store_true",
        help="Commit+push vault docs/ if pages_build changed files",
    )
    parser.add_argument("--with-telegram", action="store_true")
    args = parser.parse_args()

    # 1) Scrape / download (exit 0 even when no new circulars)
    daily_cmd = [sys.executable, str(ROOT / "edb_daily.py"), "--days", str(args.days)]
    if args.dry_run:
        daily_cmd.append("--dry-run")
    rc_daily = run(daily_cmd)
    if rc_daily != 0:
        print(f"ERROR: edb_daily failed rc={rc_daily}", flush=True)
        # Still try to bump last_synced_at so the site shows we attempted a sync
        run(
            [
                sys.executable,
                str(ROOT / "pages_build.py"),
                "--out",
                str(PAGES_OUT),
                "--write-individual",
            ]
        )
        return rc_daily

    # 2) IA upload
    if not args.skip_ia and not args.dry_run:
        ia = ROOT / "ia_upload_run.py"
        if ia.is_file():
            run([sys.executable, str(ia)])
        else:
            print("WARN: ia_upload_run.py missing; skip IA", flush=True)

    # 3) Summarize (if queue has work) + ALWAYS pages_build → last_synced_at
    notify_cmd = [sys.executable, str(ROOT / "notify_pipeline.py")]
    if args.dry_run:
        notify_cmd.append("--dry-run")
    if args.skip_summarize:
        notify_cmd.append("--skip-summarize")
    if args.with_telegram:
        notify_cmd.append("--with-telegram")
    notify_cmd.extend(["--pages-out", str(PAGES_OUT)])
    rc = run(notify_cmd)

    # 4) Optional push so GitHub Pages visitors see the new timestamp
    if args.push and not args.dry_run:
        prc = push_pages_if_changed()
        if prc != 0:
            rc = prc

    print(f"\n=== daily_pipeline finished rc={rc} ===", flush=True)
    print("Note: last_synced_at is written on every pages_build, including empty syncs.", flush=True)
    return rc


if __name__ == "__main__":
    sys.exit(main())
