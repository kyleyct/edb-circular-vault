#!/usr/bin/env python3
"""
EDB 通告備份 — Internet Archive Uploader
對應 EDB Circular Bot Project Plan v0.2 §7.2 + §17 — IA Uploader

將 data/snapshots/*.json 的 metadata + 對應 PDF 上傳到 Internet Archive
archive.org,提供永久 mirror (解決 EDB 站 360 日後清除問題)。

Setup:
    pip install --user internetarchive
    註冊 IA account: https://archive.org/account
    攞 S3-like keys: https://archive.org/account/s3.php
    設定 env:
        export IA_ACCESS_KEY="your_access_key"
        export IA_SECRET_KEY="your_secret_key"
    (或者用 `ia configure` interactive)

Usage:
    # 預設(讀 data/snapshots/full_360d_zh-HK.json, upload 落 edb-circulars-<year>)
    python3 tools/ia_uploader.py

    # 自定 input
    python3 tools/ia_uploader.py --input data/snapshots/full_360d_zh-HK.json

    # 自定 item prefix
    python3 tools/ia_uploader.py --item-prefix edb-circulars

    # Dry-run（只 print plan，不 upload）
    python3 tools/ia_uploader.py --dry-run
"""
import argparse
import json
import os
import re
import sys
import time
import logging
from datetime import date, datetime, timezone
from pathlib import Path

try:
    import internetarchive as ia
except ImportError:
    print("ERROR: 請先 pip install --user internetarchive", file=sys.stderr)
    sys.exit(2)

# ============ Config ============
WORKSPACE = Path("/Users/apple/.mavis/sessions/mvs_b78623d5503c46fe86d75edf7cf816d4/workspace")
DEFAULT_INPUT = WORKSPACE / "data" / "snapshots" / "full_360d_zh-HK.json"
DEFAULT_PDF_DIR = WORKSPACE / "pdfs"
DEFAULT_ITEM_PREFIX = "edb-circulars"
RATE_LIMIT_SEC = 5.0  # IA 對批量 upload 建議
RETRY_MAX = 5
UPLOADER_VERSION = "0.2.0"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
log = logging.getLogger("ia_uploader")


# ============ Auth ============
def check_credentials():
    """Check IA credentials in env."""
    access = os.environ.get("IA_ACCESS_KEY")
    secret = os.environ.get("IA_SECRET_KEY")
    if not access or not secret:
        log.error("缺少 IA credentials. 請設定:")
        log.error("  export IA_ACCESS_KEY='your_access_key'")
        log.error("  export IA_SECRET_KEY='your_secret_key'")
        log.error("  (註冊: https://archive.org/account, 攞 keys: https://archive.org/account/s3.php)")
        return False
    return True


# ============ Item Metadata ============
def build_item_metadata(year: int, count: int) -> dict:
    """Item-level metadata for edb-circulars-<year>."""
    return {
        "title": f"EDB Circulars {year}",
        "creator": "Education Bureau, HKSAR Government",
        "publisher": "Education Bureau, HKSAR Government",
        "date": str(year),
        "language": "zh-HK",
        "licenseurl": "https://creativecommons.org/publicdomain/zero/1.0/",
        "rights": "Metadata: CC0 1.0. PDF: © Education Bureau, archive use only.",
        "description": (
            f"Mirror of Education Bureau circulars issued in {year}, "
            f"archived from https://applications.edb.gov.hk/circular/circular.aspx?langno=2. "
            f"Contains {count} EDB circulars. See project: "
            f"https://github.com/USER/edb-circular-vault"
        ),
        "subject": ["Education", "Hong Kong", "EDB", "Circular", "Open Data", "Archive"],
        "collection": "opensource",
    }


def build_file_metadata(circular: dict) -> dict:
    """Per-file metadata for one PDF upload."""
    return {
        "title": circular.get("title", ""),
        "date": circular.get("issue_date", ""),
        "description": (circular.get("summary") or "")[:500],
        "subject": circular.get("distribution", []),
        "language": circular.get("lang", "zh-HK"),
        "source_url": circular.get("source_url", ""),
        "circular_no": circular.get("circular_no", ""),
        "scraper_version": circular.get("scraper_version", ""),
    }


# ============ Upload ============
def upload_pdf(item, pdf_path: Path, circular: dict, max_retry: int = RETRY_MAX) -> tuple:
    """Upload single PDF with retry. Return (success, error_msg)."""
    metadata = build_file_metadata(circular)
    for attempt in range(1, max_retry + 1):
        try:
            time.sleep(RATE_LIMIT_SEC)
            resp = item.upload_file(
                str(pdf_path),
                metadata=metadata,
                queue_derive=True,  # IA 自動 generate derivatives (OCR, thumbnail, etc.)
                verify=True,
            )
            if resp.status_code == 200:
                return True, None
            else:
                return False, f"HTTP {resp.status_code}: {resp.content[:200]}"
        except Exception as e:
            log.warning(f"  Upload fail {pdf_path.name} attempt {attempt}/{max_retry}: {e}")
            if attempt < max_retry:
                time.sleep(5 * (2 ** (attempt - 1)))  # 5, 10, 20, 40, 80 sec
    return False, f"Failed after {max_retry} attempts"


# ============ Main ============
def main():
    parser = argparse.ArgumentParser(description="EDB Circular Backup — IA Uploader")
    parser.add_argument("--input", type=str, default=str(DEFAULT_INPUT),
                        help="Input metadata JSON (from scraper.py)")
    parser.add_argument("--pdf-dir", type=str, default=str(DEFAULT_PDF_DIR),
                        help="PDF directory")
    parser.add_argument("--item-prefix", type=str, default=DEFAULT_ITEM_PREFIX,
                        help=f"IA item name prefix (default: {DEFAULT_ITEM_PREFIX})")
    parser.add_argument("--dry-run", action="store_true",
                        help="只 print plan，不 upload")
    parser.add_argument("--max-files", type=int, default=None,
                        help="限制 upload file 數量 (for testing)")
    args = parser.parse_args()

    # 1. 讀 input
    input_path = Path(args.input)
    if not input_path.exists():
        log.error(f"Input not found: {input_path}")
        sys.exit(1)
    with open(input_path, encoding="utf-8") as f:
        data = json.load(f)
    circulars = data.get("circulars", [])
    log.info(f"讀 input: {input_path.name}, {len(circulars)} 份")

    if not circulars:
        log.error("No circulars to upload")
        sys.exit(1)

    # 2. 依年份 group
    by_year: dict = {}
    for c in circulars:
        issue_date = c.get("issue_date", "")
        m = re.match(r"^(\d{4})-", issue_date)
        year = int(m.group(1)) if m else date.today().year
        by_year.setdefault(year, []).append(c)
    log.info(f"年份分組: {sorted(by_year.keys())}")

    # 3. Dry-run preview
    if args.dry_run:
        log.info("=" * 60)
        log.info("DRY RUN — 不會實際 upload")
        log.info("=" * 60)
        for year, items in sorted(by_year.items()):
            item_name = f"{args.item_prefix}-{year}"
            log.info(f"  Item: {item_name}  ({len(items)} 份)")
            log.info(f"    URL: https://archive.org/details/{item_name}")
        sys.exit(0)

    # 4. Check credentials
    if not check_credentials():
        sys.exit(2)

    # 5. Upload by year
    pdf_dir = Path(args.pdf_dir)
    total_uploaded = 0
    total_failed = 0
    started = time.time()
    upload_log = []

    for year, items in sorted(by_year.items()):
        item_name = f"{args.item_prefix}-{year}"
        log.info("=" * 60)
        log.info(f"=== Upload to {item_name} ({len(items)} 份) ===")
        log.info("=" * 60)

        item = ia.get_item(item_name)
        if not item.exists:
            log.info(f"Item 不存在，創建: {item_name}")
            item.modify_metadata(build_item_metadata(year, len(items)))

        for i, c in enumerate(items, 1):
            if args.max_files and i > args.max_files:
                log.info(f"  --max-files={args.max_files} reached, stop")
                break
            cid = c.get("circular_id")
            pdf_filename = f"{cid}_{c.get('lang', 'zh-HK')}.pdf"
            pdf_path = pdf_dir / pdf_filename
            if not pdf_path.exists():
                log.warning(f"  [{i}/{len(items)}] {cid}: PDF 不存在，skip ({pdf_path})")
                total_failed += 1
                continue
            log.info(f"  [{i}/{len(items)}] {cid} -> {pdf_path.name} ({pdf_path.stat().st_size} bytes)")
            ok, err = upload_pdf(item, pdf_path, c)
            if ok:
                total_uploaded += 1
                upload_log.append({"circular_id": cid, "status": "ok", "file": pdf_filename})
            else:
                total_failed += 1
                upload_log.append({"circular_id": cid, "status": "fail", "error": err})
                log.warning(f"    {cid} FAIL: {err}")

    # 6. Final report
    duration = time.time() - started
    log.info("=" * 60)
    log.info(f"IA Upload 完成: uploaded={total_uploaded}, failed={total_failed}, duration={duration:.1f}s")
    log.info("=" * 60)
    for year, items in sorted(by_year.items()):
        item_name = f"{args.item_prefix}-{year}"
        log.info(f"  https://archive.org/details/{item_name}")

    # 7. Save upload log
    log_path = input_path.parent.parent / "ia_upload_log.json"
    log_path.write_text(json.dumps({
        "input": str(input_path.relative_to(WORKSPACE)),
        "uploader_version": UPLOADER_VERSION,
        "uploaded_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "duration_sec": round(duration, 2),
        "uploaded": total_uploaded,
        "failed": total_failed,
        "details": upload_log,
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    log.info(f"Upload log: {log_path}")

    return 0 if total_failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
