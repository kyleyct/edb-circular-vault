#!/usr/bin/env python3
"""
EDB Circular Vault — Telegram channel notifier.

Reads summaries/*.json not yet in notify_state.json, formats HTML messages,
sends via Bot API when TELEGRAM_BOT_TOKEN + TELEGRAM_CHANNEL_ID are set;
otherwise (or with --dry-run) prints the message.

Usage:
  python3 telegram_notify.py --dry-run --limit 2
  python3 telegram_notify.py

Env:
  TELEGRAM_BOT_TOKEN
  TELEGRAM_CHANNEL_ID   (@channel or -100…)
"""
from __future__ import annotations

import argparse
import html
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime
from pathlib import Path
from typing import Any

_SCRIPT_DIR = Path(__file__).resolve().parent
_DEFAULT_ROOT = _SCRIPT_DIR.parent if _SCRIPT_DIR.name == "tools" else _SCRIPT_DIR
ROOT = Path(__import__("os").environ.get("EDB_WATCH_ROOT", str(_DEFAULT_ROOT)))
SUM_DIR = ROOT / "summaries"
META_DIR = ROOT / "metadata"
STATE_FILE = ROOT / "notify_state.json"
DISCLAIMER = "非官方 LLM 摘要，內容以教育局原文為準。"


def log(msg: str) -> None:
    print(msg, flush=True)


def load_state() -> dict[str, Any]:
    if not STATE_FILE.exists():
        return {"notified": {}}
    try:
        return json.loads(STATE_FILE.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"notified": {}}


def save_state(state: dict[str, Any]) -> None:
    STATE_FILE.write_text(
        json.dumps(state, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def load_metadata(cid: str) -> dict[str, Any]:
    p = META_DIR / f"{cid}.json"
    if p.exists():
        return json.loads(p.read_text(encoding="utf-8"))
    return {}


def ia_url(cid: str, year: int | None = None) -> str:
    if year is None:
        # EDBCM26xxx → 2026
        m = None
        if cid.startswith("EDBCM") and len(cid) >= 7 and cid[5:7].isdigit():
            yy = int(cid[5:7])
            year = 2000 + yy if yy < 80 else 1900 + yy
        else:
            year = datetime.now().year
    return f"https://archive.org/download/edb-circulars-{year}/{cid}.pdf"


def ia_available(url: str, timeout: float = 8.0) -> bool:
    """HEAD check; treat 404 / errors as unavailable (omit IA line)."""
    try:
        req = urllib.request.Request(url, method="HEAD")
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return 200 <= getattr(resp, "status", 200) < 400
    except Exception:
        # Some IA endpoints dislike HEAD; try a tiny GET range via GET
        try:
            req = urllib.request.Request(url, method="GET")
            req.add_header("Range", "bytes=0-0")
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                code = getattr(resp, "status", 200)
                return code in (200, 206)
        except Exception:
            return False


def esc(s: str) -> str:
    return html.escape(s or "", quote=False)


def format_html(
    summary: dict[str, Any],
    md: dict[str, Any] | None = None,
    *,
    check_ia: bool = True,
) -> str:
    md = md or {}
    links = summary.get("_links") or {}
    cid = summary.get("circular_id") or md.get("circular_id") or "?"
    title = summary.get("title_clean") or md.get("title") or cid
    issue_date = links.get("issue_date") or md.get("issue_date") or "—"
    groups = links.get("distribution_groups") or md.get("distribution_groups") or []
    dist = "／".join(groups) if groups else "—"
    pdf_url = links.get("pdf_url") or md.get("pdf_url") or ""
    one = summary.get("one_liner") or ""
    points = summary.get("key_points") or []
    action = summary.get("action_for_schools") or ""
    parent = summary.get("parent_note") or ""
    source = (summary.get("_meta") or {}).get("source") or "llm"
    disc = DISCLAIMER
    if source == "offline_fallback":
        disc = "粗略摘錄（非 LLM），內容以教育局原文為準。"

    lines = [
        f"📢 <b>{esc(cid)}</b>｜{esc(title)}",
        f"日期：{esc(str(issue_date))}｜分發：{esc(dist)}",
        "",
        f"一句：{esc(one)}",
        "",
        "<b>重點</b>",
    ]
    for p in points:
        lines.append(f"• {esc(str(p))}")
    lines += [
        "",
        f"學校可做：{esc(action)}",
        f"家長：{esc(parent)}",
        "",
    ]
    if pdf_url:
        lines.append(f'🔗 原文（EDB）：<a href="{esc(pdf_url)}">{esc(pdf_url)}</a>')
    else:
        lines.append("🔗 原文（EDB）：（未有連結）")

    # IA optional — only if reachable (skip probe when check_ia=False)
    ia = ia_url(cid)
    if check_ia and ia_available(ia):
        lines.append(f'📦 歸檔（IA）：<a href="{esc(ia)}">{esc(ia)}</a>')
    # else omit IA line (admin-hold / missing / dry-run skip)

    lines += [
        f"⚠️ {esc(disc)}",
        '專案：<a href="https://github.com/kyleyct/edb-circular-vault">edb-circular-vault</a>',
    ]
    return "\n".join(lines)


def send_message(token: str, chat_id: str, text: str) -> dict[str, Any]:
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": True,
    }
    data = urllib.parse.urlencode(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        # Surface retry_after if present
        try:
            err = json.loads(body)
            params = (err.get("parameters") or {})
            if "retry_after" in params:
                raise RuntimeError(
                    f"Telegram 429 retry_after={params['retry_after']}: {body[:300]}"
                ) from e
        except json.JSONDecodeError:
            pass
        raise RuntimeError(f"Telegram HTTP {e.code}: {body[:500]}") from e


def list_pending(limit: int = 0) -> list[Path]:
    state = load_state()
    notified = state.get("notified") or {}
    paths = sorted(SUM_DIR.glob("EDBCM*.json"), key=lambda x: x.stat().st_mtime, reverse=True)
    pending = [p for p in paths if p.stem not in notified]
    if limit and limit > 0:
        pending = pending[:limit]
    return pending


def notify_one(
    path: Path,
    *,
    dry_run: bool,
    token: str | None,
    channel: str | None,
    skip_ia_check: bool = False,
) -> bool:
    cid = path.stem
    summary = json.loads(path.read_text(encoding="utf-8"))
    md = load_metadata(cid)

    text = format_html(summary, md, check_ia=not skip_ia_check)

    if dry_run or not token or not channel:
        reason = "dry-run" if dry_run else "TELEGRAM_* unset"
        log(f"\n===== [{reason}] {cid} =====\n{text}\n===== end =====")
        return True

    log(f"Sending {cid} → {channel} …")
    result = send_message(token, channel, text)
    if not result.get("ok"):
        log(f"  ✗ send failed: {result}")
        return False

    msg_id = (result.get("result") or {}).get("message_id")
    state = load_state()
    state.setdefault("notified", {})[cid] = {
        "at": datetime.now().isoformat(timespec="seconds"),
        "msg_id": msg_id,
        "channel": channel,
    }
    save_state(state)
    log(f"  ✓ notified msg_id={msg_id}; state updated")
    return True


def main() -> int:
    parser = argparse.ArgumentParser(description="EDB Telegram notifier")
    parser.add_argument("--dry-run", action="store_true", help="Print HTML; do not send; do not update state")
    parser.add_argument("--limit", type=int, default=0, help="Max pending summaries")
    parser.add_argument("--ids", default="", help="Comma-separated ids (must have summaries/)")
    parser.add_argument(
        "--skip-ia-check",
        action="store_true",
        help="Omit IA HEAD probe (faster dry-run; never adds IA line)",
    )
    args = parser.parse_args()

    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    channel = os.environ.get("TELEGRAM_CHANNEL_ID")

    if args.ids.strip():
        state = load_state()
        notified = state.get("notified") or {}
        paths = []
        for cid in [x.strip() for x in args.ids.split(",") if x.strip()]:
            sp = SUM_DIR / f"{cid}.json"
            if not sp.exists():
                log(f"WARN: no summary for {cid}")
                continue
            if cid in notified and not args.dry_run:
                log(f"skip {cid} (already notified)")
                continue
            paths.append(sp)
        if args.limit and args.limit > 0:
            paths = paths[: args.limit]
    else:
        paths = list_pending(args.limit)

    log(
        f"=== telegram_notify: {len(paths)} pending, "
        f"dry_run={args.dry_run}, token={'yes' if token else 'no'}, "
        f"channel={channel or '—'} ==="
    )
    if not paths:
        log("Nothing to notify")
        return 0

    ok = 0
    for p in paths:
        try:
            if notify_one(
                p,
                dry_run=args.dry_run,
                token=token,
                channel=channel,
                skip_ia_check=args.skip_ia_check or args.dry_run,
            ):
                ok += 1
        except Exception as e:
            log(f"ERROR {p.stem}: {e}")

    log(f"\n=== done: {ok}/{len(paths)} ===")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
