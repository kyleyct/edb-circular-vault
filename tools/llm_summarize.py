#!/usr/bin/env python3
"""
EDB Circular Vault — LLM summarizer (DeepSeek Flash).

Reads queue/ items (or metadata/*.json), calls DeepSeek OpenAI-compatible API
with model deepseek-flash, writes summaries/{id}.json.

Usage:
  python3 llm_summarize.py --dry-run --limit 2
  python3 llm_summarize.py --limit 5
  python3 llm_summarize.py --ids EDBCM26149,EDBCM26190

Env:
  DEEPSEEK_API_KEY   required for live API calls
  LLM_MODEL          default deepseek-flash
  DEEPSEEK_BASE_URL  default https://api.deepseek.com
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import urllib.error
import urllib.request
from datetime import datetime
from pathlib import Path
from typing import Any

_SCRIPT_DIR = Path(__file__).resolve().parent
_DEFAULT_ROOT = _SCRIPT_DIR.parent if _SCRIPT_DIR.name == "tools" else _SCRIPT_DIR
ROOT = Path(__import__("os").environ.get("EDB_WATCH_ROOT", str(_DEFAULT_ROOT)))
QUEUE_DIR = ROOT / "queue"
META_DIR = ROOT / "metadata"
PDF_DIR = ROOT / "pdfs"
SUM_DIR = ROOT / "summaries"
PROMPT_FILE = ROOT / "prompts" / "edb_summary_zh_hk.txt"
if not PROMPT_FILE.exists():
    _alt = _SCRIPT_DIR.parent / "prompts" / "edb_summary_zh_hk.txt"
    if _alt.exists():
        PROMPT_FILE = _alt

DEFAULT_MODEL = "deepseek-flash"
DEFAULT_BASE = "https://api.deepseek.com"
MAX_CHARS = 10000  # ~8–12k; mid of range
DISCLAIMER = "非官方摘要，以教育局原文為準。"


def log(msg: str) -> None:
    print(msg, flush=True)


def load_prompt_parts() -> tuple[str, str]:
    """Split prompt file into system rules and user template."""
    text = PROMPT_FILE.read_text(encoding="utf-8")
    system = text
    user_tmpl = (
        "請摘要以下教育局通函。\n\n"
        "circular_id: {{circular_id}}\n"
        "issue_date: {{issue_date}}\n"
        "distribution_groups: {{distribution_groups}}\n"
        "pdf_url: {{pdf_url}}\n\n"
        "--- 通函正文（可能已截斷）---\n"
        "{{body_text}}\n"
        "--- 正文結束 ---\n\n"
        "按 SYSTEM 規則輸出 JSON。"
    )
    # Prefer explicit SYSTEM / USER TEMPLATE sections if present
    m_sys = re.search(
        r"## SYSTEM\s*\n(.*?)(?=\n## HARD RULES|\n## USER TEMPLATE|\Z)",
        text,
        re.S,
    )
    m_hard = re.search(
        r"## HARD RULES\s*\n(.*?)(?=\n## USER TEMPLATE|\Z)",
        text,
        re.S,
    )
    m_user = re.search(r"## USER TEMPLATE\s*\n(.*)\Z", text, re.S)
    if m_sys:
        parts = [m_sys.group(1).strip()]
        if m_hard:
            parts.append("HARD RULES:\n" + m_hard.group(1).strip())
        system = "\n\n".join(parts)
    if m_user:
        user_tmpl = m_user.group(1).strip()
    return system, user_tmpl


def truncate_text(text: str, max_chars: int = MAX_CHARS) -> str:
    if not text:
        return ""
    text = text.strip()
    if len(text) <= max_chars:
        return text
    # Prefer keeping an early「摘要」section if present
    head = text[:max_chars]
    # Try to cut at paragraph boundary
    cut = head.rfind("\n\n")
    if cut > max_chars * 0.6:
        head = head[:cut]
    return head + "\n\n[…正文已截斷…]"


def extract_pdf_text(pdf_path: Path | None) -> str:
    if not pdf_path or not pdf_path.exists():
        return ""
    try:
        r = subprocess.run(
            ["pdftotext", "-layout", str(pdf_path), "-"],
            capture_output=True,
            text=True,
            timeout=60,
            check=False,
        )
        if r.returncode == 0 and r.stdout.strip():
            return r.stdout
    except (FileNotFoundError, subprocess.TimeoutExpired, OSError) as e:
        log(f"  WARN: pdftotext failed for {pdf_path.name}: {e}")
    return ""


def resolve_local_path(path_str: str | None, fallback_dir: Path, cid: str, suffix: str) -> Path | None:
    """Prefer local ROOT paths; old queue entries may point at another machine."""
    if path_str:
        p = Path(path_str)
        if p.exists():
            return p
    local = fallback_dir / f"{cid}{suffix}"
    if local.exists():
        return local
    return None


def load_metadata(cid: str, metadata_path: str | None = None) -> dict[str, Any]:
    path = resolve_local_path(metadata_path, META_DIR, cid, ".json")
    if path is None:
        path = META_DIR / f"{cid}.json"
    if not path.exists():
        return {"circular_id": cid}
    return json.loads(path.read_text(encoding="utf-8"))


def collect_queue_items() -> list[dict[str, Any]]:
    """Load unique circulars from all queue_*.json files (newest first)."""
    seen: set[str] = set()
    items: list[dict[str, Any]] = []
    files = sorted(QUEUE_DIR.glob("queue_*.json"), reverse=True)
    for qf in files:
        try:
            data = json.loads(qf.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as e:
            log(f"WARN: skip queue {qf.name}: {e}")
            continue
        for it in data.get("items") or []:
            cid = it.get("circular_id")
            if not cid or cid in seen:
                continue
            seen.add(cid)
            items.append(it)
    return items


def collect_from_metadata(ids: list[str] | None = None) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    if ids:
        paths = [META_DIR / f"{i}.json" for i in ids]
    else:
        paths = sorted(META_DIR.glob("EDBCM*.json"))
    for p in paths:
        if not p.exists():
            log(f"WARN: missing metadata {p.name}")
            continue
        cid = p.stem
        items.append(
            {
                "circular_id": cid,
                "metadata_path": str(p),
                "pdf_path": str(PDF_DIR / f"{cid}.pdf"),
            }
        )
    return items


def guess_title_clean(md: dict[str, Any], body: str) -> str:
    """Heuristic title from body when metadata.title is a file-ref line."""
    title = (md.get("title") or "").strip()
    # Skip file-number / short junk titles
    bad_title = (
        not title
        or re.search(r"檔\s*號|檔號", title)
        or len(title) < 6
        or re.search(r"^─|備辦|副本送|分發名單", title)
        or title.endswith("校長") and len(title) < 20
    )
    if body:
        lines = [ln.strip() for ln in body.splitlines() if ln.strip()]
        # Normalize spaced CJK often seen in EDB PDFs: "戲 劇 節" → keep as-is for display
        candidates: list[str] = []
        after_header = False
        for ln in lines[:60]:
            if re.search(r"通\s*函\s*第|教育局通函", ln):
                after_header = True
                continue
            if re.match(r"^摘要", ln):
                break
            if re.search(r"分發名單|副本送|檔\s*號|檔號", ln):
                continue
            if after_header and 4 < len(re.sub(r"\s+", "", ln)) < 60:
                candidates.append(ln)
        if candidates:
            # Prefer the longest substantive line after header (usually the subject)
            best = max(candidates, key=lambda s: len(re.sub(r"\s+", "", s)))
            return re.sub(r"[ \t]+", "", best) if best.count(" ") >= 3 else best
        for ln in lines[:60]:
            compact = re.sub(r"\s+", "", ln)
            if re.search(r"(年度|計劃|申請|比賽|活動|課程|津貼|獎|節)", compact) and 6 < len(compact) < 60:
                if not re.search(r"檔號|分發名單|副本送|詳情|摘要", compact):
                    return compact if ln.count(" ") >= 3 else ln
    if not bad_title and len(title) < 80:
        return title
    return md.get("circular_id", "未命名通函")


def offline_summary(cid: str, md: dict[str, Any], body: str) -> dict[str, Any]:
    """Extractive fallback when LLM unavailable / dry-run."""
    raw = (md.get("summary") or body or "")[:400].replace("\n", " ").strip()
    # Prefer text after 摘要
    m = re.search(r"摘要\s*([\s\S]{20,300})", body or md.get("summary") or "")
    if m:
        chunk = m.group(1)
        chunk = re.split(r"詳情|\n\s*\d+\.", chunk, maxsplit=1)[0]
        one = re.sub(r"\s+", "", chunk).strip()
        # Prefer first sentence
        if "。" in one:
            one = one.split("。")[0] + "。"
        one = one[:80]
        if one and not one.endswith(("。", "…")):
            one = one[:79] + "…"
    else:
        one = (raw[:77] + "…") if len(raw) > 80 else (raw or "（通函正文不足，無法摘要）")

    groups = md.get("distribution_groups") or []
    title_clean = guess_title_clean(md, body or md.get("summary") or "")
    key_points: list[str] = []
    # Prefer 摘要 paragraph sentences over file-ref noise
    src = body or md.get("summary") or ""
    abs_m = re.search(r"摘要\s*([\s\S]{30,400}?)(?=詳情|\n\s*\d+\.|$)", src)
    abs_text = re.sub(r"\s+", "", abs_m.group(1)) if abs_m else ""
    if abs_text:
        # split on 。
        parts = [x for x in re.split(r"。", abs_text) if len(x) >= 8]
        for part in parts[:3]:
            key_points.append((part + "。")[:60])
    if not key_points and raw:
        cleaned = re.sub(r"檔\s*號[^\n]{0,40}", "", raw)
        cleaned = re.sub(r"\s+", " ", cleaned).strip()
        if cleaned:
            key_points.append(cleaned[:60])
    if groups:
        key_points.append("分發：" + "／".join(groups))
    if md.get("issue_date"):
        key_points.append(f"發出日期：{md['issue_date']}")
    while len(key_points) < 3:
        key_points.append("詳情請參閱教育局原文通函。")
    key_points = key_points[:5]

    return {
        "circular_id": cid,
        "title_clean": title_clean,
        "one_liner": one[:80],
        "who_should_care": list(groups) if groups else ["學校"],
        "key_points": key_points,
        "deadlines": [],
        "action_for_schools": "校長／相關統籌查閱通函詳情並按指示備辦。",
        "parent_note": "家長一般無需直接行動；如有需要學校會另行通知。",
        "disclaimer": DISCLAIMER,
        "_meta": {
            "source": "offline_fallback",
            "model": None,
            "generated_at": datetime.now().isoformat(timespec="seconds"),
            "note": "粗略摘錄，非 LLM",
        },
    }


def build_user_message(tmpl: str, cid: str, md: dict[str, Any], body: str) -> str:
    return (
        tmpl.replace("{{circular_id}}", cid)
        .replace("{{issue_date}}", str(md.get("issue_date") or ""))
        .replace(
            "{{distribution_groups}}",
            "／".join(md.get("distribution_groups") or []) or "（未列）",
        )
        .replace("{{pdf_url}}", str(md.get("pdf_url") or ""))
        .replace("{{body_text}}", body)
    )


def parse_llm_json(content: str) -> dict[str, Any]:
    content = content.strip()
    # Strip optional markdown fences
    if content.startswith("```"):
        content = re.sub(r"^```(?:json)?\s*", "", content)
        content = re.sub(r"\s*```$", "", content)
    # Find first { ... last }
    start = content.find("{")
    end = content.rfind("}")
    if start < 0 or end <= start:
        raise ValueError("no JSON object in LLM response")
    return json.loads(content[start : end + 1])


def validate_summary(obj: dict[str, Any], cid: str) -> dict[str, Any]:
    required = [
        "circular_id",
        "title_clean",
        "one_liner",
        "who_should_care",
        "key_points",
        "deadlines",
        "action_for_schools",
        "parent_note",
        "disclaimer",
    ]
    out: dict[str, Any] = {}
    for k in required:
        out[k] = obj.get(k)
    out["circular_id"] = cid
    if not isinstance(out["who_should_care"], list):
        out["who_should_care"] = [str(out["who_should_care"] or "學校")]
    if not isinstance(out["key_points"], list):
        out["key_points"] = [str(out["key_points"] or "")]
    if not isinstance(out["deadlines"], list):
        out["deadlines"] = []
    out["one_liner"] = str(out.get("one_liner") or "")[:80]
    out["key_points"] = [str(p)[:60] for p in out["key_points"][:5]]
    if len(out["key_points"]) < 3:
        out["key_points"].append("詳情請參閱教育局原文通函。")
    out["disclaimer"] = DISCLAIMER
    if not out.get("title_clean"):
        out["title_clean"] = cid
    return out


def call_deepseek(system: str, user: str, model: str, api_key: str, base_url: str) -> str:
    url = base_url.rstrip("/") + "/v1/chat/completions"
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "temperature": 0.2,
        "response_format": {"type": "json_object"},
    }
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=90) as resp:
        raw = resp.read().decode("utf-8")
    parsed = json.loads(raw)
    return parsed["choices"][0]["message"]["content"]


def summarize_one(
    item: dict[str, Any],
    *,
    dry_run: bool,
    system: str,
    user_tmpl: str,
    model: str,
    api_key: str | None,
    base_url: str,
    force: bool,
) -> dict[str, Any] | None:
    cid = item["circular_id"]
    out_path = SUM_DIR / f"{cid}.json"
    if out_path.exists() and not force and not dry_run:
        log(f"  skip {cid} (summary exists)")
        return json.loads(out_path.read_text(encoding="utf-8"))

    md = load_metadata(cid, item.get("metadata_path"))
    pdf_path = resolve_local_path(item.get("pdf_path") or md.get("pdf_path"), PDF_DIR, cid, ".pdf")
    body = extract_pdf_text(pdf_path)
    if not body:
        body = md.get("summary") or ""
        log(f"  WARN: {cid} no PDF text; using metadata.summary ({len(body)} chars)")
    body_trunc = truncate_text(body)

    if dry_run or not api_key:
        if dry_run:
            log(f"  [dry-run] {cid}: would send {len(body_trunc)} chars to {model}; offline fallback:")
        else:
            log(f"  WARN: no DEEPSEEK_API_KEY; offline fallback for {cid}")
        summary = offline_summary(cid, md, body)
        summary["_links"] = {
            "pdf_url": md.get("pdf_url"),
            "issue_date": md.get("issue_date"),
            "distribution_groups": md.get("distribution_groups") or [],
        }
        print(json.dumps(summary, ensure_ascii=False, indent=2))
        # Write offline artifact so telegram_notify / pipeline can consume it.
        # dry-run still never calls the API.
        if dry_run or not api_key:
            SUM_DIR.mkdir(parents=True, exist_ok=True)
            out_path.write_text(
                json.dumps(summary, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            log(f"  ✓ wrote {out_path.name} (offline; dry_run={dry_run})")
        return summary

    user = build_user_message(user_tmpl, cid, md, body_trunc)
    last_err: Exception | None = None
    content = ""
    for attempt in range(2):
        try:
            content = call_deepseek(system, user, model, api_key, base_url)
            obj = parse_llm_json(content)
            summary = validate_summary(obj, cid)
            summary["_meta"] = {
                "source": "deepseek",
                "model": model,
                "generated_at": datetime.now().isoformat(timespec="seconds"),
                "input_chars": len(body_trunc),
                "attempt": attempt + 1,
            }
            # Attach useful links for telegram_notify
            summary["_links"] = {
                "pdf_url": md.get("pdf_url"),
                "issue_date": md.get("issue_date"),
                "distribution_groups": md.get("distribution_groups") or [],
            }
            SUM_DIR.mkdir(parents=True, exist_ok=True)
            out_path.write_text(
                json.dumps(summary, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            log(f"  ✓ wrote {out_path.name}")
            return summary
        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, KeyError, ValueError, json.JSONDecodeError) as e:
            last_err = e
            log(f"  LLM attempt {attempt + 1} failed for {cid}: {e}")
            if attempt == 0:
                user = (
                    user
                    + "\n\n前回輸出唔係合法 JSON。請只輸出一個 JSON object，唔好加 markdown。"
                )

    log(f"  FALLBACK offline for {cid} after LLM errors: {last_err}")
    summary = offline_summary(cid, md, body)
    summary["_links"] = {
        "pdf_url": md.get("pdf_url"),
        "issue_date": md.get("issue_date"),
        "distribution_groups": md.get("distribution_groups") or [],
    }
    SUM_DIR.mkdir(parents=True, exist_ok=True)
    out_path.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    log(f"  ✓ wrote {out_path.name} (offline fallback)")
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description="EDB LLM summarizer (DeepSeek Flash)")
    parser.add_argument("--dry-run", action="store_true", help="Print offline fallback; no API; still write summaries/ for notify dry-run")
    parser.add_argument("--limit", type=int, default=0, help="Max items to process (0=all)")
    parser.add_argument("--ids", default="", help="Comma-separated circular ids (bypass queue)")
    parser.add_argument("--from-metadata", action="store_true", help="Use all metadata/*.json if queue empty")
    parser.add_argument("--force", action="store_true", help="Overwrite existing summaries")
    parser.add_argument("--model", default=os.environ.get("LLM_MODEL", DEFAULT_MODEL))
    args = parser.parse_args()

    if args.model == "deepseek-chat":
        log("ERROR: deepseek-chat is retired; use deepseek-flash")
        return 2

    system, user_tmpl = load_prompt_parts()
    api_key = os.environ.get("DEEPSEEK_API_KEY")
    base_url = os.environ.get("DEEPSEEK_BASE_URL", DEFAULT_BASE)

    if args.ids.strip():
        id_list = [x.strip() for x in args.ids.split(",") if x.strip()]
        items = collect_from_metadata(id_list)
    else:
        items = collect_queue_items()
        if not items or args.from_metadata:
            if not items:
                log("Queue empty; falling back to metadata/")
            items = collect_from_metadata()

    # Prefer items that do not yet have summaries (unless force/dry-run)
    if not args.force and not args.dry_run:
        pending = [it for it in items if not (SUM_DIR / f"{it['circular_id']}.json").exists()]
        if pending:
            items = pending

    if args.limit and args.limit > 0:
        items = items[: args.limit]

    log(
        f"=== llm_summarize: {len(items)} item(s), model={args.model}, "
        f"dry_run={args.dry_run}, key={'yes' if api_key else 'no'} ==="
    )
    if not items:
        log("Nothing to summarize")
        return 0

    SUM_DIR.mkdir(parents=True, exist_ok=True)
    ok = 0
    for it in items:
        log(f"\n--- {it['circular_id']} ---")
        try:
            result = summarize_one(
                it,
                dry_run=args.dry_run,
                system=system,
                user_tmpl=user_tmpl,
                model=args.model,
                api_key=api_key,
                base_url=base_url,
                force=args.force,
            )
            if result:
                ok += 1
        except Exception as e:
            log(f"  ERROR {it['circular_id']}: {e}")

    log(f"\n=== done: {ok}/{len(items)} ===")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
