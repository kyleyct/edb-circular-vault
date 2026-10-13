# GitHub Pages — 通告摘要站（MVP）

繁中靜態站：列表最新通告摘要，外連教育局 PDF／Internet Archive。**唔託管 PDF。**

## 本地預覽

```bash
# 1) 由 watch 摘要產生 data/
cd /workspace/edb-watch
python3 pages_build.py \
  --out /workspace/github-apply/edb-circular-vault/docs/data \
  --csv /workspace/github-apply/edb-circular-vault/data/circulars.csv \
  --write-individual

# 2) 起靜態 server（必須 HTTP，唔好用 file://）
cd /workspace/github-apply/edb-circular-vault/docs
python3 -m http.server 8080
# 瀏覽器開 http://127.0.0.1:8080/
```

Repo 內亦可：

```bash
python3 tools/pages_build.py --summaries-dir /path/to/summaries --out docs/data --write-individual
```

## 啟用 GitHub Pages

1. 開 [kyleyct/edb-circular-vault](https://github.com/kyleyct/edb-circular-vault) → **Settings → Pages**
2. **Build and deployment → Source**: Deploy from a branch
3. Branch 選 `main` 或 `pages-mvp`；folder 選 **`/docs`**
4. Save → 約數分鐘後：`https://kyleyct.github.io/edb-circular-vault/`

建議先喺 `pages-mvp` 預覽，滿意再 merge 去 `main`。

## 檔案

| 路徑 | 說明 |
|---|---|
| `docs/index.html` | 列表 UI（繁中） |
| `docs/assets/style.css` | 樣式 |
| `docs/data/summaries.json` | 聚合摘要（建站資料） |
| `docs/data/{id}.json` | 可選單份 |
| `tools/pages_build.py` | 由 `summaries/*.json` 產生上述 data |

## 同每日 pipeline 接駁

本地 watch（`/workspace/edb-watch`）：

```text
edb_daily.py → llm_summarize.py → pages_build.py →（可選）telegram_notify.py
```

`notify_pipeline.py` 會喺 summarize 之後跑 `pages_build.py`（可用 `--skip-pages` 關閉）。

更新公開站：commit／push `docs/data/summaries.json`（及個別 JSON 若有）。

## 免責

非官方開源摘要，與教育局無關；內容以 [EDB 通告站](https://applications.edb.gov.hk/circular/circular.aspx?langno=2) 原文為準。

## 最後同步時間（empty sync）

`summaries.json` 每次 `pages_build` 都會寫入 `last_synced_at`（同 `generated_at`）。
即使當日冇新通告，pipeline 都要 rebuild + push，網站先會顯示「最後同步」。

建議 Grok Bot / cron（HKT）：**08:45**、**18:45**。本地 orchestrator：`edb-watch/daily_pipeline.py --push`。

