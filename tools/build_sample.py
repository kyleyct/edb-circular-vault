#!/usr/bin/env python3
"""
Build sample metadata.json from W1 PoC results, validate against schema.

對應 EDB Circular Bot Project Plan v0.2 §6.4 — 將 W1 PoC 嘅 circulars normalize 至
符合 data/schema/metadata.schema.json 嘅格式,並產生 validate report。

Usage:
    python3 tools/build_sample.py
"""
import json
import sys
import subprocess
import re
import os
from pathlib import Path
from datetime import datetime, timezone

# Paths
WORKSPACE = Path("/Users/apple/.mavis/sessions/mvs_b78623d5503c46fe86d75edf7cf816d4/workspace")
POC_RESULT = WORKSPACE / "poc_output" / "poc_result.json"
SCHEMA = WORKSPACE / "data" / "schema" / "metadata.schema.json"
SAMPLE_OUT = WORKSPACE / "data" / "snapshots" / "w1_poc_sample.json"
REPORT_OUT = WORKSPACE / "data" / "schema" / "w1_validate_report.json"

# Master metadata header (CC0 1.0)
TOOL = "EDB Circular Vault"
TOOL_VERSION = "0.2.0"
SOURCE = "Education Bureau, HKSAR Government"
SOURCE_URL = "https://www.edb.gov.hk/tc/about-edb/forms-and-circulars/index.html"
LICENSE = "CC0 1.0 Universal (Public Domain Dedication) - metadata only"
ATTRIBUTION = "資料來源:教育局(https://www.edb.gov.hk/)。本工具僅提供 metadata 索引,PDF 透過 Internet Archive 永久 mirror。"
DISCLAIMER = "本工具非官方 open data 索引工具,與教育局無關。如發現資料與 EDB 官網不一致,以 EDB 官網為準。開發者不對因使用本工具而產生嘅任何損失負責。"


def normalize_date(issue_date: str) -> str:
    """Convert dd/mm/yyyy → YYYY-MM-DD."""
    if not issue_date:
        return None
    m = re.match(r"^(\d{1,2})/(\d{1,2})/(\d{4})$", issue_date.strip())
    if not m:
        return issue_date  # 唔識 format, keep original (validate 會 catch)
    d, mo, y = m.groups()
    return f"{y}-{int(mo):02d}-{int(d):02d}"


def normalize_distribution(dist: str) -> list:
    """Split '中學, 小學, ...' by comma → ['中學', '小學', ...]."""
    if not dist:
        return []
    return [d.strip() for d in dist.split(",") if d.strip()]


def normalize_circular(c: dict) -> dict:
    """Normalize W1 circular entry to schema-compliant format."""
    pdf_links = c.get("pdf_links", {})
    # W1 揀咗 zh-HK, 但 schema 入面 lang 係 per-circular
    # 如果有 multi-lang links, 預設取 zh-HK, lang = "zh-HK"
    lang = "zh-HK"
    source_url = pdf_links.get(lang) or next(iter(pdf_links.values()), None)

    # pdf_size_bytes 從 file size
    pdf_path_rel = c.get("pdf_path")
    pdf_size = None
    if pdf_path_rel:
        pdf_full = WORKSPACE / pdf_path_rel
        if pdf_full.exists():
            pdf_size = pdf_full.stat().st_size

    return {
        "circular_id": c.get("circular_id"),
        "circular_no": c.get("circular_no"),
        "title": (c.get("title") or "").strip(),
        "issue_date": normalize_date(c.get("issue_date")),
        "lang": lang,
        "distribution": normalize_distribution(c.get("distribution")),
        "subject": None,
        "summary": (c.get("summary") or "").strip() or None,
        "source_url": source_url,
        "archive_url": None,  # 一期 null, 待 T3
        "archive_metadata_url": None,
        "pdf_size_bytes": pdf_size,
        "pdf_pages": None,  # W1 冇 extract, 一期 null (可從 file command 拎)
        "pdf_sha256": c.get("pdf_sha256"),
        "scraped_at": c.get("scraped_at"),
        "scraper_version": "0.1.0",  # W1 PoC version
    }


def main():
    # 1. 讀 W1 PoC results
    if not POC_RESULT.exists():
        print(f"ERROR: {POC_RESULT} not found", file=sys.stderr)
        sys.exit(1)
    with open(POC_RESULT, encoding="utf-8") as f:
        poc = json.load(f)
    print(f"讀 W1 PoC: {POC_RESULT.name}, {poc.get('success_count', 0)} 份")

    # 2. Normalize 5 份
    normalized = [normalize_circular(c) for c in poc.get("results", [])]
    print(f"Normalized {len(normalized)} 份")

    # 3. 寫 sample metadata file
    sample = {
        "schema_version": "1.0",
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "tool": TOOL,
        "tool_version": TOOL_VERSION,
        "source": SOURCE,
        "source_url": SOURCE_URL,
        "license": LICENSE,
        "attribution": ATTRIBUTION,
        "disclaimer": DISCLAIMER,
        "circulars": normalized,
    }
    SAMPLE_OUT.parent.mkdir(parents=True, exist_ok=True)
    with open(SAMPLE_OUT, "w", encoding="utf-8") as f:
        json.dump(sample, f, ensure_ascii=False, indent=2)
    print(f"Wrote sample: {SAMPLE_OUT}")

    # 4. Validate
    print(f"\nValidating {SAMPLE_OUT.name} against {SCHEMA.name}...")
    sys.path.insert(0, str(WORKSPACE / "tools"))
    import validate
    valid, errors, schema, instance = validate.validate_file(str(SCHEMA), str(SAMPLE_OUT))

    # 5. 寫 report
    report = {
        "validated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "schema": str(SCHEMA.relative_to(WORKSPACE)),
        "instance": str(SAMPLE_OUT.relative_to(WORKSPACE)),
        "valid": valid,
        "error_count": len(errors),
        "errors": errors,
        "circular_count": len(normalized),
    }
    REPORT_OUT.parent.mkdir(parents=True, exist_ok=True)
    with open(REPORT_OUT, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    if valid:
        print(f"OK: {len(normalized)} 份全部通過 schema 驗證")
        print(f"Report: {REPORT_OUT}")
        sys.exit(0)
    else:
        print(f"FAIL: {len(errors)} 個 errors")
        for e in errors:
            print(f"  - {e}")
        print(f"\nReport: {REPORT_OUT}")
        sys.exit(1)


if __name__ == "__main__":
    main()
