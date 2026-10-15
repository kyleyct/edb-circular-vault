> **2026-10-10 更新**：發佈優先改為 **GitHub Pages**（見 [PAGES.md](PAGES.md)）。 Telegram 仍可選；本文件保留 bot 設定說明。

# EDB Telegram + LLM 通知（MVP）

本地 watch 目錄：`/workspace/edb-watch`  
對應計劃：`/workspace/plans/edb-telegram-llm-notify-plan.md`

## 用途

在每日 `edb_daily.py`（detect → download → metadata → `queue/`）之後：

1. **`llm_summarize.py`** — 讀 queue／metadata，用 DeepSeek **`deepseek-flash`** 產生繁中結構化摘要 → `summaries/{id}.json`  
2. **`telegram_notify.py`** — 讀未發佈摘要，HTML 發去 Telegram Channel；`notify_state.json` 保證不重複發  
3. **`notify_pipeline.py`** — 上述兩步一條指令

## 環境變數

```bash
# 已有（box）
export DEEPSEEK_API_KEY=…          # 必填先可以真打 API
# export POE_API_KEY=…             # 預留 fallback（MVP 未接）

# Kyle 建 bot／channel 後先加（不要 commit）
export TELEGRAM_BOT_TOKEN=…
export TELEGRAM_CHANNEL_ID=@edb_circular_hk   # 或 -100…

# 可選
export LLM_MODEL=deepseek-flash    # 不要用已退役的 deepseek-chat
export DEEPSEEK_BASE_URL=https://api.deepseek.com
```

**Secrets 不入 git。** `.env`／box env only。

## 用法

```bash
cd /workspace/edb-watch

# Dry-run：offline 摘要 + 印 Telegram HTML，不打 API、不 send
python3 notify_pipeline.py --dry-run --limit 2

# 指定通函
python3 notify_pipeline.py --dry-run --ids EDBCM26149,EDBCM26190

# Live：打 DeepSeek；有 TELEGRAM_* 就 send，沒有就印訊息
python3 notify_pipeline.py --limit 5

# 分開跑
python3 llm_summarize.py --limit 3
python3 telegram_notify.py --dry-run --limit 3
```

## 檔案

| 路徑 | 說明 |
|---|---|
| `prompts/edb_summary_zh_hk.txt` | System／user prompt 規則 |
| `llm_summarize.py` | DeepSeek Flash → `summaries/` |
| `telegram_notify.py` | HTML sendMessage + `notify_state.json` |
| `notify_pipeline.py` | summarize then notify |
| `summaries/*.json` | 摘要產物（可本地保留；公開 repo 另議） |
| `notify_state.json` | 已通知 idempotency |

## 每日 routine 建議順序（08:45 HKT）

```text
1) python3 edb_daily.py --days 7
2) python3 ia_upload_run.py          # 失敗不阻 notify
3) python3 notify_pipeline.py
```

## Kyle 下一步（一次人手）

1. `@BotFather` → `/newbot` → 拎 `TELEGRAM_BOT_TOKEN`  
2. 建 public channel（例如「教育局通告速報（非官方）」）→ bot 設 **Admin + Post messages**  
3. 設 `TELEGRAM_CHANNEL_ID`（`@username` 或 `-100…`）  
4. 驗收：`curl -s "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/getMe"`  
5. 再跑 `python3 notify_pipeline.py --limit 1`（不加 `--dry-run`）

## 免責

非官方開源摘要，與教育局無關；內容以 [EDB 通告站](https://applications.edb.gov.hk/circular/circular.aspx?langno=2) 原文為準。  
專案：https://github.com/kyleyct/edb-circular-vault
