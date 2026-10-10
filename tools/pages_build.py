#!/usr/bin/env python3
"""
EDB Circular Vault — build GitHub Pages data from local summaries.

Reads summaries/*.json (+ optional metadata/ and vault circulars.csv for links),
writes docs/data/summaries.json and optionally per-id JSON copies.

Usage:
  python3 pages_build.py
  python3 pages_build.py --summaries-dir ./summaries --out ./docs/data
  python3 pages_build.py --out /workspace/github-apply/edb-circular-vault/docs/data \\
                         --csv /workspace/github-apply/edb-circular-vault/data/circulars.csv \\
                         --write-individual
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

HK = ZoneInfo("Asia/Hong_Kong")
ROOT = Path(__file__).resolve().parent

DEFAULT_DISCLAIMER = "非官方 AI 摘要，以教育局原文為準。本站不託管 PDF。"
EDB_PDF_TMPL = "https://applications.edb.gov.hk/circular/upload/EDBCM/{id}C.pdf"
IA_DL_TMPL = "https://archive.org/download/edb-circulars-{year}/{id}_zh-HK.pdf"


def parse_issue_date(s: str | None) -> tuple:
    """Return sortable tuple; unknown dates sort last."""
    if not s:
        return (0, 0, 0)
    s = s.strip()
    for fmt in ("%d/%m/%Y", "%Y-%m-%d", "%Y/%m/%d"):
        try:
            d = datetime.strptime(s, fmt)
            return (d.year, d.month, d.day)
        except ValueError:
            continue
    return (0, 0, 0)


def year_from_id(circular_id: str) -> int | None:
    m = re.match(r"EDBCM(\d{2})", circular_id or "")
    if not m:
        return None
    yy = int(m.group(1))
    return 2000 + yy if yy < 100 else yy


def load_csv_links(csv_path: Path | None) -> dict[str, dict]:
    out: dict[str, dict] = {}
    if not csv_path or not csv_path.is_file():
        return out
    with csv_path.open(encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            cid = (row.get("circular_id") or "").strip()
            if not cid:
                continue
            out[cid] = {
                "edb_url": (row.get("source_url") or "").strip() or None,
                "ia_url": (row.get("archive_url") or "").strip() or None,
                "title": (row.get("title") or "").strip() or None,
                "issue_date": (row.get("issue_date") or "").strip() or None,
            }
    return out


def load_metadata(meta_dir: Path, cid: str) -> dict:
    p = meta_dir / f"{cid}.json"
    if not p.is_file():
        return {}
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def public_item(
    raw: dict,
    meta: dict,
    csv_row: dict | None,
    include_guessed_ia: bool,
) -> dict:
    cid = raw.get("circular_id") or meta.get("circular_id") or ""
    links = raw.get("_links") or {}
    csv_row = csv_row or {}

    edb_url = (
        csv_row.get("edb_url")
        or links.get("pdf_url")
        or meta.get("pdf_url")
        or (EDB_PDF_TMPL.format(id=cid) if cid else None)
    )
    ia_url = csv_row.get("ia_url") or links.get("ia_url") or meta.get("archive_url")
    if not ia_url and include_guessed_ia and cid:
        y = year_from_id(cid)
        if y:
            ia_url = IA_DL_TMPL.format(year=y, id=cid)

    issue_date = (
        links.get("issue_date")
        or meta.get("issue_date")
        or csv_row.get("issue_date")
        or ""
    )
    # Normalize ISO date from CSV (2026-09-18) to DD/MM/YYYY for UI consistency
    if re.match(r"^\d{4}-\d{2}-\d{2}$", issue_date):
        y, m, d = issue_date.split("-")
        issue_date = f"{d}/{m}/{y}"

    gen = (raw.get("_meta") or {}).get("generated_at") or raw.get("generated_at")

    return {
        "circular_id": cid,
        "title_clean": raw.get("title_clean") or csv_row.get("title") or meta.get("title") or cid,
        "one_liner": raw.get("one_liner") or "",
        "who_should_care": list(raw.get("who_should_care") or links.get("distribution_groups") or meta.get("distribution_groups") or []),
        "key_points": list(raw.get("key_points") or []),
        "deadlines": list(raw.get("deadlines") or []),
        "action_for_schools": raw.get("action_for_schools") or "",
        "parent_note": raw.get("parent_note") or "",
        "disclaimer": raw.get("disclaimer") or "非官方摘要，以教育局原文為準。",
        "issue_date": issue_date,
        "edb_url": edb_url,
        "ia_url": ia_url,
        "generated_at": gen,
        "source": (raw.get("_meta") or {}).get("source"),
    }


def build(
    summaries_dir: Path,
    meta_dir: Path,
    out_dir: Path,
    csv_path: Path | None,
    write_individual: bool,
    include_guessed_ia: bool,
) -> dict:
    csv_links = load_csv_links(csv_path)
    items: list[dict] = []

    files = sorted(summaries_dir.glob("*.json"))
    for path in files:
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as e:
            print(f"WARN: skip {path.name}: {e}", flush=True)
            continue
        cid = raw.get("circular_id") or path.stem
        meta = load_metadata(meta_dir, cid)
        item = public_item(raw, meta, csv_links.get(cid), include_guessed_ia)
        items.append(item)

    items.sort(
        key=lambda it: (parse_issue_date(it.get("issue_date")), it.get("circular_id") or ""),
        reverse=True,
    )

    payload = {
        "generated_at": datetime.now(HK).isoformat(timespec="seconds"),
        "source": "edb-circular-vault",
        "disclaimer": DEFAULT_DISCLAIMER,
        "count": len(items),
        "items": items,
    }

    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "summaries.json"
    out_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"Wrote {out_path} ({len(items)} items)", flush=True)

    if write_individual:
        for it in items:
            cid = it["circular_id"]
            if not cid:
                continue
            p = out_dir / f"{cid}.json"
            p.write_text(json.dumps(it, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"Wrote {len(items)} individual JSON under {out_dir}", flush=True)

    return payload


def main() -> int:
    parser = argparse.ArgumentParser(description="Build GitHub Pages summaries.json")
    parser.add_argument(
        "--summaries-dir",
        type=Path,
        default=ROOT / "summaries",
        help="Directory of per-circular summary JSON",
    )
    parser.add_argument(
        "--metadata-dir",
        type=Path,
        default=ROOT / "metadata",
        help="Local metadata/ from edb_daily",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=None,
        help="Output directory for summaries.json (default: sibling vault docs/data or ./docs/data)",
    )
    parser.add_argument(
        "--csv",
        type=Path,
        default=None,
        help="Optional vault circulars.csv for EDB/IA URLs",
    )
    parser.add_argument(
        "--write-individual",
        action="store_true",
        help="Also write docs/data/{id}.json",
    )
    parser.add_argument(
        "--guess-ia",
        action="store_true",
        default=True,
        help="If no archive_url, guess IA download URL (default on)",
    )
    parser.add_argument(
        "--no-guess-ia",
        action="store_true",
        help="Do not guess IA URLs",
    )
    args = parser.parse_args()

    out = args.out
    if out is None:
        candidates = [
            Path("/workspace/github-apply/edb-circular-vault/docs/data"),
            ROOT.parent / "github-apply" / "edb-circular-vault" / "docs" / "data",
            ROOT / "docs" / "data",
        ]
        out = next((c for c in candidates if c.parent.is_dir() or c.parent.parent.is_dir()), candidates[-1])

    csv_path = args.csv
    if csv_path is None:
        for c in [
            Path("/workspace/github-apply/edb-circular-vault/data/circulars.csv"),
            ROOT.parent / "github-apply" / "edb-circular-vault" / "data" / "circulars.csv",
        ]:
            if c.is_file():
                csv_path = c
                break

    if not args.summaries_dir.is_dir():
        print(f"ERROR: summaries dir not found: {args.summaries_dir}", file=sys.stderr)
        return 1

    include_guessed = args.guess_ia and not args.no_guess_ia
    build(
        summaries_dir=args.summaries_dir,
        meta_dir=args.metadata_dir,
        out_dir=out,
        csv_path=csv_path,
        write_individual=args.write_individual,
        include_guessed_ia=include_guessed,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
