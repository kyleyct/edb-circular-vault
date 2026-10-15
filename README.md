# EDB Circular Vault — 教育局通告 Open Data 索引

> 為香港教育界提供永久可訪問的 EDB 通告 metadata 索引

[![License: CC0 for data](https://img.shields.io/badge/data-CC0%201.0-blue.svg)](LICENSE-CC0)
[![License: MIT for code](https://img.shields.io/badge/code-MIT-green.svg)](LICENSE-MIT)

## 為何有這個 project？

教育局通告站(`applications.edb.gov.hk/circular/circular.aspx?langno=2`)只保留**過去 360 日**（一年）的通告，過期即清除。對於需要跨年比較、查找過往政策的教師、行政主任、政策研究員而言，這個 retention 不足。

本工具透過雙軌架構,將 EDB 通告永久 archive:

- **GitHub**(本 repo):託管 metadata(`data/metadata.json` + `data/circulars.csv`),以 **CC0 1.0** 公開
- **Internet Archive**:永久 mirror EDB 原始 PDF,透過 [archive.org/details/edb-circulars-\<year\>](https://archive.org/) 提供永久訪問

GitHub 不 host 任何 PDF，所有 PDF 連結到 Internet Archive。私隱 + 法律風險歸零。

## 通告摘要站（GitHub Pages MVP）

繁中靜態列表（教師／家長）：AI／自動摘要 + 連去 EDB／IA，**不 host PDF**。

- 本地預覽：`cd docs && python3 -m http.server 8080` → http://127.0.0.1:8080/
- 建資料：`python3 tools/pages_build.py --summaries-dir /path/to/summaries --out docs/data --write-individual`
- 啟用說明：[`docs/PAGES.md`](docs/PAGES.md)
- 計劃：Pages-first；Telegram 可選（見 `docs/telegram-notify.md`）
- 同步建議（HKT）：**08:45** 及 **18:45**；即使沒有新通告都要 rebuild Pages 以更新 `last_synced_at`（見 `docs/PAGES.md`）

---

## 點樣用?

### 查通告

- **瀏覽**:`data/circulars.csv`(spreadsheet view, 187 份繁中通告,過去 360 日)
- **JSON API**:`data/metadata.json`(結構化, 對應 `data/schema/metadata.schema.json`)
- **GitHub 搜尋**:用 GitHub 內置搜尋 box 查 `data/circulars.csv`
- **Command line**:
  ```bash
  grep "公民教育" data/circulars.csv
  ```

### 拎 PDF

任何 circular 的 `source_url` 對應 EDB 站 PDF；`archive_url` 對應 Internet Archive 永久 mirror。Internet Archive 上有原檔 + IA 自動生成的衍生檔（OCR text, thumbnails, etc.）。

### 本地 mirror

```bash
# 從 Internet Archive 下載所有 PDF 落本地
python3 tools/ia_uploader.py --download-only

# 或從 EDB 站直接 scrape
python3 tools/scraper.py --days 360 --lang zh-HK
```

## 點樣 contribute?

### 報錯 metadata

- 用 [Issue template](.github/ISSUE_TEMPLATE/data_correction.md) 報錯某份通告的 metadata(標題、日期、分發組別等)
- 或直接 PR 修改 `data/metadata.json`

### 翻譯 / 改良 docs

- PR 到 `docs/` (繁中為主,歡迎英文版)
- 修正 README、FAQ、schema 的錯別字

### 改良 scraper

- PR 到 `tools/scraper.py`
- 加新 features(例如:LLM 主題標註、新 language support)

### 上載 PDF 落 Internet Archive

- 註冊 IA account: <https://archive.org/account>
- 攞 S3 keys: <https://archive.org/account/s3.php>
- 設定 env: `IA_ACCESS_KEY` / `IA_SECRET_KEY`
- 跑: `python3 tools/ia_uploader.py --input data/snapshots/full_360d_zh-HK.json`

## 點樣 build?

### 安裝依賴

```bash
# Python 3.12+
pip install --user internetarchive  # 只 IA uploader 需要
# tools/ 全部其他 scripts 係 stdlib only
# tools/scraper.py 需要 beautifulsoup4 + lxml
pip install --user beautifulsoup4 lxml
```

### 跑 scraper(增量, default 7 日)

```bash
python3 tools/scraper.py
```

### 跑 scraper(完整 360 日, --force 重 scrape)

```bash
python3 tools/scraper.py --days 360 --force --lang zh-HK
```

### Validate metadata

```bash
python3 tools/validate.py data/schema/metadata.schema.json data/metadata.json
```

## License

- **`data/` 內的 metadata**：`CC0 1.0 Universal` — 放棄我們部分版權，任何人都可商業 / 非商業 reuse
- **`tools/` 及 `docs/` 內的 source code / 文檔**：`MIT License`
- **EDB 通告 PDF 本身**:© 教育局版權所有,透過 Internet Archive mirror 供 archive / 研究用途

## 資料來源

- [香港特別行政區教育局](https://www.edb.gov.hk/)
- [Internet Archive](https://archive.org/)
- Project plan: [v0.2](EDB-Circular-Bot-Project-Plan-v0.2.md)

## 免責聲明

本工具為**非官方** open data 索引工具,與教育局無關。

如發現資料與 EDB 官網不一致,**以 EDB 官網為準**。本工具開發者不對因使用本工具而產生的任何損失負責。

Internet Archive 的 mirror 雖永久但非 100% 保證，建議用戶自備本地備份（用 `tools/scraper.py`）。

## 開發者

由獨立開發者於 2026 年 6 月開始,作為香港教育界 open data contribution 的個人項目。

如有問題或建議,請開 [Issue](../../issues)。

## Telegram 通告速報（非官方，MVP）

自動繁中摘要 → Telegram Channel。詳見 [`docs/telegram-notify.md`](docs/telegram-notify.md)。

本地執行環境暫時以 watch 目錄為準；`tools/llm_summarize.py`、`tools/telegram_notify.py`、`tools/notify_pipeline.py` 已同步。設定 `EDB_WATCH_ROOT` 指向有 `queue/`、`metadata/`、`pdfs/` 的目錄。

**不會**在本 repo 存放 `TELEGRAM_BOT_TOKEN`／API keys。
