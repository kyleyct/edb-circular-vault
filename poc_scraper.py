#!/usr/bin/env python3
"""
EDB 通告備份 — W1 PoC v2 (簡化版)
直接 parse 搜尋結果頁，不需要 detail 頁

每個 circular entry 結構 (一個 <tr>):
  td1: 日期 (dd/mm/yyyy)
  td2: 主題 (標題) + 通告編號 + 摘要 + 學校類別
  td3: 語言 (E/C/S 三個 PDF 連結)
"""
import sys as _sys
print("=== POC v2 DEBUG MARKER ===", file=_sys.stderr, flush=True)
print(f"=== file: {__file__} ===", file=_sys.stderr, flush=True)
import urllib.request
import urllib.parse
import urllib.error
import http.cookiejar
import json
import re
import sys
import time
import hashlib
import logging
from datetime import date
from pathlib import Path
from bs4 import BeautifulSoup

# ============ Config ============
BASE_URL = "https://applications.edb.gov.hk/circular/circular.aspx?langno=2"
LANGNO = 2
USER_AGENT = "EDB-Circular-Backup-Tool/0.1 (+PoC; indie-dev)"

WORKSPACE = Path("/Users/apple/.mavis/sessions/mvs_b78623d5503c46fe86d75edf7cf816d4/workspace")
OUT = WORKSPACE / "poc_output"
OUT.mkdir(parents=True, exist_ok=True)
(OUT / "pdfs").mkdir(parents=True, exist_ok=True)

PERIOD_FROM = "01/06/2024"
PERIOD_TO = date.today().strftime("%d/%m/%Y")
TARGET_COUNT = 5
RATE_LIMIT_SEC = 1.5
REQUEST_TIMEOUT = 30
RETRY_MAX = 3

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(OUT / "poc_log.txt", encoding="utf-8", mode="w"),
        logging.StreamHandler(sys.stdout),
    ],
)
log = logging.getLogger("poc")


def make_opener():
    cj = http.cookiejar.CookieJar()
    op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
    op.addheaders = [
        ("User-Agent", USER_AGENT),
        ("Accept-Language", "zh-HK,zh;q=0.9,en;q=0.8"),
        ("Accept", "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"),
    ]
    return op


def req(opener, method, url, form_data=None, max_retry=RETRY_MAX):
    headers = {
        "Referer": url,
        "Origin": "https://applications.edb.gov.hk",
    }
    if method == "POST":
        headers["Content-Type"] = "application/x-www-form-urlencoded"
        data = urllib.parse.urlencode(form_data).encode("utf-8") if form_data else b""
    else:
        data = None
    for attempt in range(1, max_retry + 1):
        try:
            time.sleep(RATE_LIMIT_SEC)
            req = urllib.request.Request(url, data=data, method=method, headers=headers)
            resp = opener.open(req, timeout=REQUEST_TIMEOUT)
            body = resp.read()
            log.info(f"{method} {url[:80]} -> {resp.status} ({len(body)} bytes) [attempt {attempt}]")
            return resp.status, body
        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, OSError) as e:
            log.warning(f"{method} fail {attempt}/{max_retry}: {type(e).__name__}: {e}")
            if attempt < max_retry:
                time.sleep(2 ** attempt)
    return None, None


def parse_circular_entries(html_text):
    """Parse 搜尋結果頁, 拎所有 circular entry (每個 <tr> 一份通告)."""
    soup = BeautifulSoup(html_text, "lxml")
    entries = []
    for tr in soup.find_all("tr"):
        tds = tr.find_all("td", class_="circularResultRow")
        if len(tds) < 3:
            continue
        # td1: 日期
        date_div = tds[0].find("div", class_="table_text_mobile_app")
        issue_date = date_div.get_text(strip=True) if date_div else None
        # td2: 主題 + 通告編號 + 摘要 + 學校類別
        topic_div = tds[1].find("div", class_="table_text_mobile_app")
        if not topic_div:
            continue
        # 標題 = 第一段文字(主旨, 在 (通告編號：...) 之前)
        topic_text = topic_div.get_text("\n", strip=True)
        # 通告編號
        m = re.search(r"通告編號[：:]\s*([A-Z0-9/]+)", topic_text)
        circular_no = m.group(1) if m else None
        # 主標題: 第一行(在 (通告編號:...) 之前)
        title = None
        for line in topic_text.split("\n"):
            line = line.strip()
            if line and not line.startswith("(") and "通告編號" not in line:
                title = line
                break
        # 摘要
        summary = None
        m = re.search(r"摘要[：:](.+?)(?:學校類別|$)", topic_text, re.DOTALL)
        if m:
            summary = " ".join(m.group(1).split())[:500]
        # 學校類別
        m = re.search(r"學校類別[：:]\s*(.+)", topic_text)
        distribution = " ".join(m.group(1).split()) if m else None
        # td3: PDF 連結
        pdf_links = {}
        for a in tds[2].find_all("a", href=True):
            href = a["href"]
            text = a.get_text(strip=True)
            # Match ../circular/upload/EDBCM/XXXX[C|E|S].pdf
            m = re.search(r"upload/(EDBCM|EDBC)/([A-Z0-9]+)([CES])\.pdf", href, re.IGNORECASE)
            if not m:
                continue
            lang_suffix = m.group(3).upper()
            lang_map = {"E": "en", "C": "zh-HK", "S": "zh-CN"}
            lang_code = lang_map.get(lang_suffix, lang_suffix)
            full_url = urllib.parse.urljoin(BASE_URL, href)
            pdf_links[lang_code] = full_url
        if not pdf_links:
            continue
        # Derive circular_id (file basename w/o lang suffix)
        first_url = next(iter(pdf_links.values()))
        m = re.search(r"/([A-Z]+[0-9]+)[CES]\.pdf", first_url, re.IGNORECASE)
        circular_id = m.group(1) if m else circular_no
        entries.append({
            "circular_id": circular_id,
            "circular_no": circular_no,
            "title": title,
            "issue_date": issue_date,
            "distribution": distribution,
            "summary": summary,
            "pdf_links": pdf_links,
        })
    # Dedup by circular_id
    seen = set()
    unique = []
    for e in entries:
        if e["circular_id"] in seen:
            continue
        seen.add(e["circular_id"])
        unique.append(e)
    return unique


def download_pdf(opener, url, save_path):
    status, data = req(opener, "GET", url)
    if status != 200 or not data:
        return False, None
    if not data.startswith(b"%PDF"):
        log.warning(f"  PDF magic 不正確, first 20 bytes = {data[:20]!r}")
        return False, None
    save_path.write_bytes(data)
    return True, hashlib.sha256(data).hexdigest()


def main():
    started = time.time()
    log.info("=" * 60)
    log.info(f"EDB 通告備份 PoC v2 — 目標 {TARGET_COUNT} 份 (langno=2, {PERIOD_FROM} ~ {PERIOD_TO})")
    log.info("=" * 60)

    # Step 1: GET list page (拎 VIEWSTATE)
    opener = make_opener()
    status, html = req(opener, "GET", BASE_URL)
    if status != 200:
        log.error("GET 列表頁 fail")
        return finalize(started, False, error="GET list fail")
    soup = BeautifulSoup(html.decode("utf-8", "replace"), "lxml")
    vs = {
        k: soup.find("input", {"name": k})["value"]
        for k in ["__VIEWSTATE", "__EVENTVALIDATION", "__VIEWSTATEGENERATOR"]
        if soup.find("input", {"name": k})
    }
    vs["__EVENTTARGET"] = ""
    vs["__EVENTARGUMENT"] = ""
    vs["__LASTFOCUS"] = ""
    log.info(f"VIEWSTATE: {len(vs.get('__VIEWSTATE',''))} chars")

    # Step 2: POST 搜尋表單
    form = dict(vs)
    form.update({
        "ctl00$MainContentPlaceHolder$txtKeyword": "",
        "ctl00$MainContentPlaceHolder$ddlSchoolType2": "",
        "ctl00$MainContentPlaceHolder$ddlCircularType": "",
        "ctl00$MainContentPlaceHolder$txtCircularNumber": "",
        "ctl00$MainContentPlaceHolder$txtPeriodFrom": PERIOD_FROM,
        "ctl00$MainContentPlaceHolder$txtPeriodTo": PERIOD_TO,
        "ctl00$MainContentPlaceHolder$btnSearch2": "搜尋",
    })
    status, html = req(opener, "POST", BASE_URL, form)
    if status != 200:
        log.error("POST 搜尋 fail")
        return finalize(started, False, error="POST search fail")
    html_text = html.decode("utf-8", "replace")
    (OUT / "search_result.html").write_text(html_text, encoding="utf-8")

    # Step 3: Parse entries
    entries = parse_circular_entries(html_text)
    log.info(f"搵到 {len(entries)} 份通告 entries")
    if not entries:
        return finalize(started, False, error="No entries parsed")

    sample = entries[:TARGET_COUNT]
    log.info("=" * 60)
    log.info(f"STEP 4: 下載頭 {len(sample)} 份的繁中 PDF")
    log.info("=" * 60)

    results = []
    for i, e in enumerate(sample, 1):
        log.info(f"[{i}/{len(sample)}] {e['circular_id']} | {e['circular_no']} | {e['title']}")
        log.info(f"  date={e['issue_date']} | dist={e['distribution']}")
        # 用繁中 (zh-HK, suffix C) PDF
        pdf_url = e["pdf_links"].get("zh-HK") or next(iter(e["pdf_links"].values()))
        target = OUT / "pdfs" / f"{e['circular_id']}_zh-HK.pdf"
        ok, sha = download_pdf(opener, pdf_url, target)
        log.info(f"  PDF -> {target.name} ({target.stat().st_size if ok else 0} bytes) sha={sha[:16] if sha else 'N/A'}")
        results.append({**e, "pdf_path": str(target.relative_to(WORKSPACE)) if ok else None, "pdf_sha256": sha, "status": "ok" if ok else "pdf_fail"})

    success = sum(1 for r in results if r["status"] == "ok")
    return finalize(started, success > 0, success_count=success, target_count=len(sample), results=results)


def finalize(started, success, **kwargs):
    duration = time.time() - started
    summary = {
        "success": success,
        "duration_sec": round(duration, 2),
        "period": f"{PERIOD_FROM} ~ {PERIOD_TO}",
        "langno": LANGNO,
        "ua": USER_AGENT,
        "finished_at": time.strftime("%Y-%m-%d %H:%M:%S %Z"),
        **kwargs,
    }
    (OUT / "poc_result.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    log.info("=" * 60)
    log.info(f"PoC 完成: success={success}, {duration:.1f}s, OK={kwargs.get('success_count',0)}/{kwargs.get('target_count',0)}")
    log.info("=" * 60)
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
