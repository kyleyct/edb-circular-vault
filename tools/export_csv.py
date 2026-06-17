#!/usr/bin/env python3
"""
EDB 通告備份 — CSV Exporter
對應 EDB Circular Bot Project Plan v0.2 §6.4 — data/circulars.csv

將 data/snapshots/*.json 嘅 metadata 攤平成 CSV (spreadsheet view)。
用 '|' delimiter join distribution array(避免 CSV escape 嘅 quote 問題)。

Usage:
    python3 tools/export_csv.py [--input data/snapshots/full_360d_zh-HK.json] [--output data/circulars.csv]
"""
import argparse
import csv
import json
import sys
from pathlib import Path

WORKSPACE = Path("/Users/apple/.mavis/sessions/mvs_b78623d5503c46fe86d75edf7cf816d4/workspace")
DEFAULT_INPUT = WORKSPACE / "data" / "snapshots" / "full_360d_zh-HK.json"
DEFAULT_OUTPUT = WORKSPACE / "data" / "circulars.csv"

CSV_COLUMNS = [
    "circular_id",
    "circular_no",
    "issue_date",
    "title",
    "lang",
    "distribution",
    "subject",
    "summary",
    "source_url",
    "archive_url",
    "archive_metadata_url",
    "pdf_size_bytes",
    "pdf_pages",
    "pdf_sha256",
    "scraped_at",
    "scraper_version",
]


def main():
    parser = argparse.ArgumentParser(description="EDB Circular Metadata → CSV")
    parser.add_argument("--input", type=str, default=str(DEFAULT_INPUT))
    parser.add_argument("--output", type=str, default=str(DEFAULT_OUTPUT))
    args = parser.parse_args()

    input_path = Path(args.input)
    output_path = Path(args.output)

    if not input_path.exists():
        print(f"ERROR: input not found: {input_path}", file=sys.stderr)
        sys.exit(1)

    with open(input_path, encoding="utf-8") as f:
        data = json.load(f)
    circulars = data.get("circulars", [])
    if not circulars:
        print("ERROR: no circulars in input", file=sys.stderr)
        sys.exit(1)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_COLUMNS, quoting=csv.QUOTE_MINIMAL)
        writer.writeheader()
        for c in circulars:
            row = {}
            for col in CSV_COLUMNS:
                v = c.get(col)
                if isinstance(v, list):
                    row[col] = "|".join(str(x) for x in v) if v else ""
                else:
                    row[col] = "" if v is None else v
            writer.writerow(row)
    print(f"Wrote {len(circulars)} 份 -> {output_path}")


if __name__ == "__main__":
    sys.exit(main())
