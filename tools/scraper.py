#!/usr/bin/env python3
"""
EDB 通告備份 — Production Scraper
對應 EDB Circular Bot Project Plan v0.2 §6.2 + §7.1 — Scraper 增強版

Features (A9-A13):
- A9: 增量 scrape (default --days 7)
- A10: 重 scrape (--force 模式, 跳過 hash dedup)
- A11: 跨年度 scrape (--from / --to)
- A12: 三語 scrape (--lang zh-HK / zh-CN / en / all)
- A13: Hash 去重 (load existing snapshots, skip 已 scrape 嘅)

Output 符合 data/schema/metadata.schema.json (CC0 metadata)。

Usage:
    # 增量 (default 7 日, 繁中)
    python3 tools/scraper.py

    # 全 360 日, 跳過 dedup (重 scrape)
    python3 tools/scraper.py --days 360 --force

    # 自定 period (yyyy-mm-dd)
    python3 tools/scraper.py --from 2024-01-01 --to 2024-12-31

    # 三語 (繁/簡/英)
    python3 tools/scraper.py --lang all

    # 唔下載 PDF (只用於 debug 結構)
    python3 tools/scraper.py --dry-run
"""
import argparse
import hashlib
import http.cookiejar
import json
import logging
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from bs4 import BeautifulSoup

# ============ Config ============
BASE_URL_TEMPLATE = "https://applications.edb.gov.hk/circular/circular.aspx?langno={langno}"
USER_AGENT = "EDB-Circular-Backup-Tool/0.2 (+https://github.com/USER/edb-circular-vault)"
LANG_MAP = {"zh-HK": 2, "zh-CN": 3, "en": 1}
LANG_FROM_SUFFIX = {"C": "zh-HK", "S": "zh-CN", "E": "en"}
DEFAULT_LANG = "zh-HK"
RATE_LIMIT_SEC = 1.5
REQUEST_TIMEOUT = 30
RETRY_MAX = 3
SCRAPER_VERSION = "0.2.0"

WORKSPACE = Path("/Users/apple/.mavis/sessions/mvs_b78623d5503c46fe86d75edf7cf816d4/workspace")
DEFAULT_PDF_DIR = WORKSPACE / "pdfs"
DEFAULT_SNAPSHOTS_DIR = WORKSPACE / "data" / "snapshots"
DEFAULT_OUTPUT_DIR = WORKSPACE / "data" / "snapshots"

LICENSE = "CC0 1.0 Universal (Public Domain Dedication) - metadata only"
ATTRIBUTION = "資料來源:教育局(https://www.edb.gov.hk/)。本工具僅提供 metadata 索引,PDF 透過 Internet Archive 永久 mirror。"
DISCLAIMER = "本工具非官方 open data 索引工具,與教育局無關。如發現資料與 EDB 官網不一致,以 EDB 官網為準。"
SOURCE = "Education Bureau, HKSAR Government"
SOURCE_URL = "https://www.edb.gov.hk/tc/about-edb/forms-and-circulars/index.html"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
log = logging.getLogger("scraper")


# ============ HTTP Client ============
class HttpClient:
    def __init__(self, langno: int):
        cj = http.cookiejar.CookieJar()
        self.opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
        self.opener.addheaders = [
            ("User-Agent", USER_AGENT),
            ("Accept-Language", "zh-HK,zh;q=0.9,en;q=0.8"),
            ("Accept", "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"),
        ]
        self.base_url = BASE_URL_TEMPLATE.format(langno=langno)

    def request(self, method: str, url: str, form_data: dict = None) -> tuple:
        headers = {"Referer": url, "Origin": "https://applications.edb.gov.hk"}
        if method == "POST":
            headers["Content-Type"] = "application/x-www-form-urlencoded"
            data = urllib.parse.urlencode(form_data).encode("utf-8") if form_data else b""
        else:
            data = None
        for attempt in range(1, RETRY_MAX + 1):
            try:
                time.sleep(RATE_LIMIT_SEC)
                req = urllib.request.Request(url, data=data, method=method, headers=headers)
                resp = self.opener.open(req, timeout=REQUEST_TIMEOUT)
                body = resp.read()
                log.debug(f"{method} {url[:80]} -> {resp.status} ({len(body)} bytes) [attempt {attempt}]")
                return resp.status, body
            except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, OSError) as e:
                log.warning(f"{method} fail {attempt}/{RETRY_MAX}: {type(e).__name__}: {e}")
                if attempt < RETRY_MAX:
                    time.sleep(2 ** attempt)
        return None, None


# ============ Search ============
def search_circulars(http: HttpClient, period_from: str, period_to: str) -> list:
    """POST 搜尋表單, 拎 circular entries (raw format)."""
    status, html = http.request("GET", http.base_url)
    if status != 200:
        log.error("GET list page fail")
        return []
    soup = BeautifulSoup(html.decode("utf-8", "replace"), "lxml")
    vs = {}
    for k in ["__VIEWSTATE", "__EVENTVALIDATION", "__VIEWSTATEGENERATOR"]:
        el = soup.find("input", {"name": k})
        if el:
            vs[k] = el["value"]
    vs["__EVENTTARGET"] = ""
    vs["__EVENTARGUMENT"] = ""
    vs["__LASTFOCUS"] = ""
    log.info(f"VIEWSTATE: {len(vs.get('__VIEWSTATE',''))} chars")

    form = dict(vs)
    form.update({
        "ctl00$MainContentPlaceHolder$txtKeyword": "",
        "ctl00$MainContentPlaceHolder$ddlSchoolType2": "",
        "ctl00$MainContentPlaceHolder$ddlCircularType": "",
        "ctl00$MainContentPlaceHolder$txtCircularNumber": "",
        "ctl00$MainContentPlaceHolder$txtPeriodFrom": period_from,
        "ctl00$MainContentPlaceHolder$txtPeriodTo": period_to,
        "ctl00$MainContentPlaceHolder$btnSearch2": "搜尋",
    })
    status, html = http.request("POST", http.base_url, form)
    if status != 200:
        log.error("POST search fail")
        return []
    return parse_circular_entries(html.decode("utf-8", "replace"))


def parse_circular_entries(html_text: str) -> list:
    """Parse 搜尋結果頁, 拎所有 circular entry (raw format)."""
    soup = BeautifulSoup(html_text, "lxml")
    entries = []
    for tr in soup.find_all("tr"):
        tds = tr.find_all("td", class_="circularResultRow")
        if len(tds) < 3:
            continue
        date_div = tds[0].find("div", class_="table_text_mobile_app")
        issue_date = date_div.get_text(strip=True) if date_div else None
        topic_div = tds[1].find("div", class_="table_text_mobile_app")
        if not topic_div:
            continue
        topic_text = topic_div.get_text("\n", strip=True)
        m = re.search(r"通告編號[：:]\s*([A-Z0-9/]+)", topic_text)
        circular_no = m.group(1) if m else None
        title = None
        for line in topic_text.split("\n"):
            line = line.strip()
            if line and not line.startswith("(") and "通告編號" not in line:
                title = line
                break
        m = re.search(r"摘要[：:](.+?)(?:學校類別|$)", topic_text, re.DOTALL)
        summary = " ".join(m.group(1).split())[:5000] if m else None
        m = re.search(r"學校類別[：:]\s*(.+)", topic_text)
        distribution_str = " ".join(m.group(1).split()) if m else None
        pdf_links = {}
        for a in tds[2].find_all("a", href=True):
            href = a["href"]
            m = re.search(r"upload/(EDBCM|EDBC)/([A-Z0-9]+)([CES])\.pdf", href, re.IGNORECASE)
            if not m:
                continue
            suffix = m.group(3).upper()
            lang_code = LANG_FROM_SUFFIX.get(suffix, suffix)
            full_url = urllib.parse.urljoin(BASE_URL_TEMPLATE.format(langno=2), href)
            pdf_links[lang_code] = full_url
        if not pdf_links:
            continue
        first_url = next(iter(pdf_links.values()))
        m = re.search(r"/([A-Z]+[0-9]+)[CES]\.pdf", first_url, re.IGNORECASE)
        circular_id = m.group(1) if m else circular_no
        distribution_list = [d.strip() for d in (distribution_str or "").split(",") if d.strip()]
        entries.append({
            "circular_id": circular_id,
            "circular_no": circular_no,
            "title": title,
            "issue_date": issue_date,
            "distribution": distribution_list,
            "summary": summary,
            "pdf_links": pdf_links,
        })
    seen = set()
    unique = []
    for e in entries:
        if e["circular_id"] in seen:
            continue
        seen.add(e["circular_id"])
        unique.append(e)
    return unique


# ============ PDF Download ============
def download_pdf(http: HttpClient, url: str, save_path: Path) -> tuple:
    status, data = http.request("GET", url)
    if status != 200 or not data:
        return False, None
    if not data.startswith(b"%PDF"):
        log.warning(f"PDF magic 唔啱, first 20 bytes = {data[:20]!r}")
        return False, None
    save_path.parent.mkdir(parents=True, exist_ok=True)
    save_path.write_bytes(data)
    return True, hashlib.sha256(data).hexdigest()


# ============ Hash Dedup ============
def load_existing_hashes(snapshots_dir: Path) -> dict:
    """{circular_id: sha256} from all snapshots."""
    hashes = {}
    if not snapshots_dir.exists():
        return hashes
    for f in snapshots_dir.glob("*.json"):
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
            for c in data.get("circulars", []):
                cid = c.get("circular_id")
                sha = c.get("pdf_sha256")
                if cid and sha:
                    hashes[cid] = sha
        except Exception as e:
            log.warning(f"Skip snapshot {f.name}: {e}")
    return hashes


# ============ Normalize ============
def normalize_date(issue_date: str) -> str:
    """dd/mm/yyyy → YYYY-MM-DD."""
    if not issue_date:
        return None
    m = re.match(r"^(\d{1,2})/(\d{1,2})/(\d{4})$", issue_date.strip())
    if not m:
        return issue_date
    d, mo, y = m.groups()
    return f"{y}-{int(mo):02d}-{int(d):02d}"


def normalize_circular(c: dict, lang: str, pdf_dir: Path) -> dict:
    """Raw entry → schema-compliant circular."""
    pdf_links = c.get("pdf_links", {})
    pdf_url = pdf_links.get(lang) or next(iter(pdf_links.values()), None)
    pdf_size = None
    if pdf_url:
        m = re.search(r"/([A-Z0-9]+)[CES]\.pdf", pdf_url, re.IGNORECASE)
        if m:
            pdf_path = pdf_dir / f"{m.group(1)}_{lang}.pdf"
            if pdf_path.exists():
                pdf_size = pdf_path.stat().st_size
    return {
        "circular_id": c.get("circular_id"),
        "circular_no": c.get("circular_no"),
        "title": (c.get("title") or "").strip(),
        "issue_date": normalize_date(c.get("issue_date")),
        "lang": lang,
        "distribution": c.get("distribution", []),
        "subject": None,
        "summary": c.get("summary"),
        "source_url": pdf_url,
        "archive_url": None,
        "archive_metadata_url": None,
        "pdf_size_bytes": pdf_size,
        "pdf_pages": None,
        "pdf_sha256": c.get("pdf_sha256"),
        "scraped_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "scraper_version": SCRAPER_VERSION,
    }


# ============ CLI ============
def main():
    parser = argparse.ArgumentParser(description="EDB Circular Backup Scraper (Production v0.2)")
    parser.add_argument("--days", type=int, default=7,
                        help="過去 N 日 (default 7, 增量). Use 360 for full year.")
    parser.add_argument("--from", dest="from_date", type=str,
                        help="Period from (YYYY-MM-DD)")
    parser.add_argument("--to", dest="to_date", type=str,
                        help="Period to (YYYY-MM-DD)")
    parser.add_argument("--lang", default=DEFAULT_LANG, choices=["zh-HK", "zh-CN", "en", "all"],
                        help=f"PDF language (default {DEFAULT_LANG})")
    parser.add_argument("--output", type=str, default=None,
                        help="Output JSON file path (default: data/snapshots/scrape_<date>.json)")
    parser.add_argument("--snapshots-dir", type=str, default=str(DEFAULT_SNAPSHOTS_DIR),
                        help="Existing snapshots dir for hash dedup")
    parser.add_argument("--pdf-dir", type=str, default=str(DEFAULT_PDF_DIR),
                        help="PDF output directory")
    parser.add_argument("--force", action="store_true", help="Skip hash dedup")
    parser.add_argument("--dry-run", action="store_true", help="Parse only, 唔下載 PDF")
    args = parser.parse_args()

    # Period
    if args.from_date and args.to_date:
        period_from = _to_edb_date(args.from_date)
        period_to = _to_edb_date(args.to_date)
    else:
        to_d = date.today()
        from_d = to_d - timedelta(days=args.days)
        period_to = to_d.strftime("%d/%m/%Y")
        period_from = from_d.strftime("%d/%m/%Y")
    log.info(f"Period: {period_from} ~ {period_to} ({args.days} days)")

    langs = ["zh-HK", "zh-CN", "en"] if args.lang == "all" else [args.lang]
    log.info(f"Languages: {langs}")

    # Hash dedup
    snapshots_dir = Path(args.snapshots_dir)
    existing = load_existing_hashes(snapshots_dir) if not args.force else {}
    log.info(f"Existing snapshots: {len(existing)} 份 (force={args.force})")

    pdf_dir = Path(args.pdf_dir)

    all_results = {}  # circular_id → normalized (zh-HK 優先)
    started = time.time()
    for lang in langs:
        log.info(f"=== Scrape lang={lang} ===")
        http = HttpClient(LANG_MAP[lang])
        entries = search_circulars(http, period_from, period_to)
        log.info(f"搵到 {len(entries)} 份 (lang={lang})")

        new_count = skip_count = fail_count = 0
        for i, entry in enumerate(entries, 1):
            cid = entry["circular_id"]
            if cid in existing and not args.force:
                skip_count += 1
                continue
            if args.dry_run:
                entry["pdf_sha256"] = None
                normalized = normalize_circular(entry, lang, pdf_dir)
                if cid not in all_results or lang == "zh-HK":
                    all_results[cid] = normalized
                new_count += 1
            else:
                pdf_url = entry.get("pdf_links", {}).get(lang)
                if not pdf_url:
                    log.warning(f"  [{i}/{len(entries)}] {cid}: no {lang} PDF, skip")
                    fail_count += 1
                    continue
                m = re.search(r"/([A-Z0-9]+)[CES]\.pdf", pdf_url, re.IGNORECASE)
                if not m:
                    log.warning(f"  [{i}/{len(entries)}] {cid}: bad URL pattern")
                    fail_count += 1
                    continue
                pdf_path = pdf_dir / f"{m.group(1)}_{lang}.pdf"
                ok, sha = download_pdf(http, pdf_url, pdf_path)
                if not ok:
                    log.warning(f"  [{i}/{len(entries)}] {cid}: PDF download fail")
                    fail_count += 1
                    continue
                entry["pdf_sha256"] = sha
                log.info(f"  [{i}/{len(entries)}] {cid} ({lang}): {pdf_path.name} ({pdf_path.stat().st_size} bytes) sha={sha[:16]}")
                normalized = normalize_circular(entry, lang, pdf_dir)
                if cid not in all_results or lang == "zh-HK":
                    all_results[cid] = normalized
                new_count += 1
        log.info(f"  lang={lang}: new={new_count}, skipped={skip_count}, failed={fail_count}")

    circulars = list(all_results.values())

    # Output
    output = {
        "schema_version": "1.0",
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "tool": "EDB Circular Vault",
        "tool_version": "0.2.0",
        "source": SOURCE,
        "source_url": SOURCE_URL,
        "license": LICENSE,
        "attribution": ATTRIBUTION,
        "disclaimer": DISCLAIMER,
        "circulars": circulars,
    }
    if args.output:
        out_path = Path(args.output)
    else:
        out_path = DEFAULT_OUTPUT_DIR / f"scrape_{date.today().isoformat()}_{args.lang}.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    duration = time.time() - started
    log.info("=" * 60)
    log.info(f"完成: {len(circulars)} 份 (dry-run={args.dry_run}), {duration:.1f}s")
    log.info(f"Output: {out_path}")
    log.info(f"PDF dir: {pdf_dir}")
    log.info("=" * 60)
    return 0


def _to_edb_date(s: str) -> str:
    """YYYY-MM-DD → dd/mm/yyyy."""
    if re.match(r"^\d{4}-\d{2}-\d{2}$", s):
        y, mo, d = s.split("-")
        return f"{int(d)}/{int(mo)}/{y}"
    return s


if __name__ == "__main__":
    sys.exit(main())
