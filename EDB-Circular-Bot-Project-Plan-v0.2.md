# 教育局通告備份與分析 Bot — 項目計劃書 v0.2

> **文件性質**: 項目經理(PM)視角嘅專案計劃書
> **對象**: 開發者本人(用戶)、未來潛在協作者、潛在 open data 貢獻者
> **撰寫日期**: 2026-06-15 (v0.1) / 2026-06-16 (v0.2)
> **版本**: v0.2 — **2026-06-16:Open Data 方案 A 落地**
> **語言**: 香港繁體書面語
> **狀態**: 等待 PM 拍板 W2 開工指令

---

## 0. 版本變更摘要 (v0.1 → v0.2)

| 變更 | v0.1 | v0.2 |
|---|---|---|
| **Storage 策略** | 未定(PM 探討中) | **方案 A:Public metadata + Internet Archive mirror**(已拍板) |
| **發佈渠道** | 隱含 private repo(跟 W1 偏好) | **Public GitHub repo** + **Internet Archive** 永久 mirror |
| **時程 W2-W4** | 完整 scraper + DuckDB + 搜尋 | 改為:Scraper + IA uploader + GitHub public repo init |
| **法律章節** | 香港政府版權一般討論 | 加入 CC0 1.0 metadata license、Internet Archive safe harbor、明示 attribution |
| **新增章節** | — | §15 Open Data 路線圖、§16 GitHub 結構、§17 IA upload 範本 |
| **PM 問題狀態** | 5 條全未答 | #2 發佈渠道(隱含答案 = public GitHub + IA)、其他 4 條 defaults 喺 §12 |

**主要 trigger**:用戶 2026-06-16 揀方案 A 處理 EDB PDF storage 問題。

---

## 1. 項目摘要 (Executive Summary)

教育局通告(EDB Circular)係香港學校教師與行政人員日常運作嘅「搵食工具」。教育局(`applications.edb.gov.hk/circular/`)只保留**過去 360 日**(一年)嘅通告,過期清除。

本項目嘅目標:**建立一個 open data 風格嘅備份與索引工具**,將 EDB 通告嘅 metadata 結構化公開,並透過 Internet Archive 永久 mirror PDF 文件,解決 EDB 站 360 日清除問題。

**2026-06-16 拍板嘅 storage 方案 — 方案 A**:
- **Public GitHub repo**:託管 metadata (JSON / CSV),結構化、可搜尋、可 contribute
- **Internet Archive**:永久 mirror EDB 原始 PDF,archive.org 嘅 safe harbor 對 archive use case 適用
- **本地快取**:用戶電腦即時 access

關鍵設計原則:
1. **Open data, not redistribute**:metadata 公開(無私隱問題),PDF 透過 Internet Archive(archive use case safe harbor),GitHub 唔 host 任何 PDF
2. **解決根本問題**:EDB 站 360 日後清除 = 通告永遠消失;Internet Archive 提供永久 mirror
3. **完全免費**:GitHub Free + Internet Archive 免費 hosting
4. **100% 本地處理**:用戶查詢、搜尋喺本地進行,公開嘅只係 metadata + 連結
5. **符合 PDPO**:唔 host 任何可能含個資嘅 PDF,只提供 archive.org 永久 mirror(用戶自行 access)

---

## 2. 問題陳述 (Problem Statement)

(同 v0.1,unchanged)

### 2.1 痛點

| 痛點 | 受影響角色 | 影響程度 |
| --- | --- | --- |
| 通告過期被清除 | 教師、校長、行政主任 | 高 — 直接影響日常工作 |
| PDF 附件散落各方 | 全校教職員 | 中 — 重複下載、版本混亂 |
| 搜尋介面唔友善 | 新入職教師 | 中 — EDB 官方搜尋體驗差 |
| 跨年份比較困難 | 政策研究員、科主任 | 高 — 無法睇 5 年走勢 |
| 訂閱/提醒機制欠奉 | 校長、行政 | 中 — 依賴 email forward |
| 簡體中文版(langno=3)亦同步運作 | 跨境教師、內地新來港 | 低 — 雙語對照需求 |

### 2.2 現有方案嘅不足

- **官方 EDB 通告頁**:只保留 360 日,搜尋只限當下一年,無 API,無 RSS
- **第三方通告轉發群組(WhatsApp/Telegram)**:只流動少量,非歸檔
- **教育界博客/KOL 整理**:零散、唔齊全,作者停更就消失
- **立法會文件系統**:只覆蓋立法會相關通告
- **Google 搜尋**:可見性低(EDB 站內 SEO 弱)

### 2.3 機會窗口 (Why Now)

- 過去幾年 EDB 通告量穩步上升
- 香港教師/行政人員對「本地工具」+「open data」接受度高
- Internet Archive 嘅 archive use case 對政府文件 safe harbor 確認
- GitHub 對 open data project 嘅 discoverability 強

---

## 3. 目標與成功指標 (Goals & KPIs)

(同 v0.1,unchanged)

### 3.1 業務目標

| 目標 | 衡量指標 | 目標值 (12 個月) |
| --- | --- | --- |
| G1: 備份完整性 | 已備份通告 / EDB 同期通告 | ≥ 99% |
| G2: 永久存取 | 用戶可透過 Internet Archive link 查詢 5 年前通告 | archive.org link 100% work |
| G3: 搜尋準確度 | 用戶搜尋「公民教育」,GitHub metadata CSV 前 5 結果命中率 | ≥ 85% |
| G4: 隱私合規 | GitHub repo 唔 host 任何 PDF,只 metadata | 100% 唔 host PDF |
| G5: Open data contribution | 第三方 PR / fork / star | ≥ 10 stars / ≥ 3 external PRs |
| G6: Internet Archive 永久性 | archive.org link uptime | ≥ 99.9% |

### 3.2 用戶目標

- **U1**(教師):「我下學期教公民科,想去 archive.org 拎返 2023 年嗰份公民教育通告。」
- **U2**(行政主任):「校長問我 2023 年 9 月嗰份通告,EDB 已清除,本工具 metadata + archive link 即時找到。」
- **U3**(校長):「想用 metadata CSV 篩選某主題通告,跨年比較。」
- **U4**(政策研究員):「5 年內 EDB 通告嘅主題分佈分析,CSV / JSON 直接 import Pandas / R。」

### 3.3 技術目標

- 每日 / 每週自動 scrape + commit metadata(GitHub Actions)
- 每次 scrape 自動 upload 新 PDF 落 Internet Archive
- archive.org link 永久可訪問
- GitHub repo pages 加 schema doc + 數據字典

### 3.4 非目標 (Non-Goals)

- ❌ GitHub host PDF(法律 + 私隱 risk,改用 IA)
- ❌ SaaS / 多用戶協作
- ❌ 即時通訊 / 評論
- ❌ 通告內容 AI 摘要(一期)
- ❌ 取代 EDB 官方搜尋(我哋係 mirror / index,非 source of truth)

---

## 4. 範圍 (Scope)

### 4.1 In Scope(本期做)

| 模塊 | 描述 |
| --- | --- |
| **Public metadata repo** | GitHub public repo 託管 `data/metadata.json` + `data/circulars.csv` |
| **Internet Archive mirror** | 自動 upload EDB PDF 落 archive.org,每份有獨立 archive.org URL |
| **Metadata 抽取** | 標題、日期、通告編號、分發組別、摘要、PDF 連結、SHA-256、archive URL |
| **跨年存取** | 預期支援 5 年+ 資料量 |
| **雙語** | 同時備份繁體(langno=2)及簡體(langno=3)版本 |
| **本地快取** | 用戶本地 mirror PDF + DuckDB metadata(供離線 access) |
| **增量更新** | 每日/每週 scrape,只 add new circular(避免重複) |
| **社群參與** | 公開 repo 接受 PR(e.g. 用戶可報錯某份通告 metadata 唔啱) |
| **Documentation** | README, schema doc, contributing guide, legal 聲明 |

### 4.2 Out of Scope(本期不做)

- ❌ GitHub host PDF(已喺 §1 同 §9 講明,改用 IA)
- ❌ Vue 3 frontend search UI(一期留俾二期;一期靠 GitHub 內置搜尋 + CSV 篩選)
- ❌ DuckDB 本地查詢(一期 user 唔需要;GitHub UI 已足夠 metadata query)
- ❌ 訂閱 / 通知機制
- ❌ LLM 主題標註
- ❌ SaaS / 雲端服務

### 4.3 階段性 scope

| 階段 | 包含 | 不包含 |
| --- | --- | --- |
| **W2-W4 (MVP)** | Scraper 完整 + IA uploader + GitHub public repo init | UI / 訂閱 |
| **W5-W8 (Enhancement)** | README polish, GitHub Actions auto-update, contributing guide | LLM 標註 |
| **二期** | Vue 3 UI, DuckDB local query, 訂閱 | SaaS |

---

## 5. 利益相關者 (Stakeholders)

(同 v0.1,加 open data community)

| 角色 | 對工具嘅期望 | 影響 / 介入度 |
| --- | --- | --- |
| **教師**(主要用戶) | 容易去 archive.org 拎過往通告 | 高 |
| **學校行政主任**(主要用戶) | 齊全 metadata,快速搜尋 | 高 |
| **校長**(次要用戶) | 篩選 + archive link | 中 |
| **科主任 / 統籌**(次要用戶) | 主題分類、跨年比較 | 中 |
| **教育界 NGO / 政策研究員**(邊緣用戶) | CSV / JSON 完整資料 export | 中 — 但係 brand 建立關鍵 |
| **Open data community** | GitHub stars / forks / PRs | 中 — 影響 discoverability |
| **Internet Archive** | archive use case 嘅被動 partner | 低 — 接受 upload |
| **教育局 EDB** | 雖然 scrape,但合理使用,未至於投訴 | 低 — 但係法律 / 禮儀關鍵 |
| **開發者(用戶本人)** | Open data contribution + 個人興趣 + 商業潛力 | 100% |

---

## 6. 技術架構 (Technical Architecture)

### 6.1 整體架構圖(方案 A)

```
┌────────────────────────────────────────────────────────────────┐
│                  三層 Open Data 架構                           │
│                                                                │
│  層 1: GitHub Public Repo (Open Data 入口)                    │
│  ┌────────────────────────────────────────┐                    │
│  │  data/metadata.json     # 結構化       │                    │
│  │  data/circulars.csv     # 表格          │                    │
│  │  data/snapshots/       # 按時 snapshot │                    │
│  │  docs/                 # schema, FAQ   │                    │
│  │  tools/                # scraper code  │                    │
│  │  README.md + LICENSE   # CC0 1.0       │                    │
│  └────────────────────────────────────────┘                    │
│                          │                                     │
│                          │ metadata field 包含                │
│                          ▼                                     │
│  層 2: Internet Archive (永久 mirror)                         │
│  ┌────────────────────────────────────────┐                    │
│  │  archive.org/details/edb-circulars-2026│                    │
│  │  ├── EDBCM26082C.pdf                  │                    │
│  │  ├── EDBCM26077C.pdf                  │                    │
│  │  └── ...                              │                    │
│  │  archive.org 提供 safe harbor          │                    │
│  └────────────────────────────────────────┘                    │
│                          ▲                                     │
│                          │ PDF source URL                      │
│  層 3: EDB 官方站 (source of truth)                            │
│  ┌────────────────────────────────────────┐                    │
│  │  applications.edb.gov.hk/circular/     │                    │
│  │  /upload/EDBCM/XXX[C|E|S].pdf         │                    │
│  └────────────────────────────────────────┘                    │
│                                                                │
│  另外:用戶電腦(本地快取)                                     │
│  ┌────────────────────────────────────────┐                    │
│  │  ./pdfs/  (mirror PDF,離線 access)     │                    │
│  │  ./metadata.db  (DuckDB,本地 query)    │                    │
│  │  [一期可選;二期先落地]                 │                    │
│  └────────────────────────────────────────┘                    │
└────────────────────────────────────────────────────────────────┘
```

### 6.2 技術棧

| 層 | 技術 | 理由 |
| --- | --- | --- |
| Scraper | Python 3.12 + httpx + BeautifulSoup4 + lxml | 沿用 W1 PoC 設計,stdlib 可 fallback |
| 排程 | GitHub Actions(cron schedule) | 免費,公開 project 標準做法 |
| Internet Archive upload | `internetarchive` Python library | 官方 library,支援 S3-like API |
| GitHub 託管 | Git + GitHub Public Repo | 免費,discoverable |
| License | CC0 1.0 Universal | open data 標準,放棄所有版權 |
| Documentation | Markdown + GitHub Pages(可選) | 標準 |
| Schema validation | JSON Schema | 確保 metadata 結構一致 |
| Tests | pytest | scraper 必須穩定 |

### 6.3 關鍵技術決策

(同 v0.1,加 storage 決策)

- **D6 (NEW): 為何 metadata public 但 PDF 唔 host?**
  - 私隱:PDF 可能含 PDPO 敏感資料
  - 法律:EDB 通告 footer 寫 "© 教育局版權所有",mass redistribution 有 risk
  - 開放:metadata 公開 = open data spirit 已達
  - 永久:Internet Archive 提供永久 mirror,EDB 站 360 日後清除都唔影響
  - 對比:host PDF 喺 GitHub = 永久私隱 + 法律 risk,no upside

- **D7 (NEW): 為何 Internet Archive 唔係其他 archive service?**
  - Internet Archive 對 archive use case 有明確 safe harbor
  - 完全免費(無 storage / bandwidth limit)
  - URL 永久
  - 已被學術界 + 政府機構信任
  - 用戶友善(簡單 web interface,直接 download)

- **D8 (NEW): 為何 CC0 1.0 而非 CC BY 4.0?**
  - Open data 黃金標準(e.g. 美國政府 open data 全用 CC0)
  - 鼓勵最大 reuse(商業 / 非商業)
  - 對 EDB 通告 metadata(事實資料,factual data)有 legal basis
  - EDB 通告內容本身仍係 © 教育局(我哋只放 metadata,非全文)
  - 註:CC0 唔影響 EDB 本身嘅 © — 仍然要 attribution 出處

### 6.4 數據模型 (Data Model)

**SQLite/DuckDB 表(本地)** + **JSON export(公開)**

```sql
CREATE TABLE circular (
  id              VARCHAR(20) PRIMARY KEY,    -- EDBC(M)編號
  circular_no     VARCHAR(50),               -- EDBCM082/2026 格式
  issue_date      DATE NOT NULL,
  title           TEXT NOT NULL,
  lang            VARCHAR(2),                 -- 'zh-HK' / 'zh-CN' / 'en'
  distribution    TEXT[],                     -- ['中學', '小學', ...]
  subject         TEXT,                       -- 一期 null,二期 LLM 標註
  summary         TEXT,
  pdf_size_bytes  INTEGER,
  pdf_pages       INTEGER,
  pdf_sha256      VARCHAR(64),
  source_url      TEXT NOT NULL,              -- EDB 站 PDF URL
  archive_url     TEXT,                       -- archive.org URL
  scraped_at      TIMESTAMP,
  scraper_version VARCHAR(20)
);
```

**公開 JSON 結構(public-facing):**

```json
{
  "schema_version": "1.0",
  "generated_at": "2026-06-16T13:00:00+08:00",
  "tool": "EDB Circular Vault",
  "tool_version": "0.1.0",
  "source": "Education Bureau, HKSAR Government",
  "source_url": "https://www.edb.gov.hk/tc/about-edb/forms-and-circulars/index.html",
  "license": "CC0 1.0 Universal (Public Domain Dedication) - metadata only",
  "attribution": "資料來源:教育局(https://www.edb.gov.hk/)。本工具僅提供 metadata 索引,PDF 透過 Internet Archive 永久 mirror。",
  "disclaimer": "本工具非官方,以 EDB 官網為準。",
  "circulars": [
    {
      "circular_id": "EDBCM26082",
      "circular_no": "EDBCM082/2026",
      "title": "由課程及質素保證科分發的學與教材料",
      "issue_date": "2026-06-15",
      "lang": "zh-HK",
      "distribution": ["中學", "小學", "資助中學", "資助小學", "英基學校", "特殊學校", "私立中學", "私立小學", "按位津貼學校", "直接資助學校", "幼稚園"],
      "subject": null,
      "summary": "本通函旨在通知各幼稚園、小學及中學校長...",
      "source_url": "https://applications.edb.gov.hk/circular/upload/EDBCM/EDBCM26082C.pdf",
      "archive_url": "https://archive.org/download/edb-circulars-2026/EDBCM26082C.pdf",
      "archive_metadata_url": "https://archive.org/details/edb-circulars-2026/EDBCM26082C",
      "pdf_size_bytes": 1175164,
      "pdf_pages": 13,
      "pdf_sha256": "1bd92cbd41d73c6f70e0c852dde5348a632eb9b252b8895ee0f1dcded06db897",
      "scraped_at": "2026-06-15T20:00:25+08:00",
      "scraper_version": "0.1.0"
    }
  ]
}
```

**CSV 結構(同 JSON,但每個 field 一 column):**

```csv
circular_id,circular_no,issue_date,title,lang,distribution,subject,summary,source_url,archive_url,pdf_size_bytes,pdf_pages,pdf_sha256,scraped_at,scraper_version
EDBCM26082,EDBCM082/2026,2026-06-15,由課程及質素保證科分發的學與教材料,zh-HK,"中學|小學|資助中學|...",,"本通函旨在通知...",https://applications.edb.gov.hk/circular/upload/EDBCM/EDBCM26082C.pdf,https://archive.org/download/edb-circulars-2026/EDBCM26082C.pdf,1175164,13,1bd92cbd41d73c6f...,2026-06-15T20:00:25+08:00,0.1.0
```

### 6.5 GitHub Repo Structure(方案 A 落地)

```
edb-circular-vault/                              # GitHub public repo
├── README.md                                    # 繁中, project 介紹
├── LICENSE                                      # CC0 1.0 Universal
├── CONTRIBUTING.md                              # 點樣 contribute
├── CODE_OF_CONDUCT.md                           # GitHub standard
├── CHANGELOG.md                                 # release notes
├── .github/
│   ├── workflows/
│   │   ├── weekly-scrape.yml                    # 每週一 09:00 HKT 自動 scrape + commit
│   │   ├── ci.yml                               # pytest + lint
│   │   └── validate-data.yml                    # JSON Schema 驗證 metadata.json
│   └── ISSUE_TEMPLATE/
│       ├── bug_report.md
│       └── data_correction.md                   # 報錯 metadata
├── data/
│   ├── metadata.json                            # master metadata(全部 circulars)
│   ├── circulars.csv                            # spreadsheet view
│   ├── snapshots/
│   │   ├── 2024.json
│   │   ├── 2025.json
│   │   └── 2026.json                            # 按年 snapshot
│   └── schema/
│       └── metadata.schema.json                 # JSON Schema 定義
├── docs/
│   ├── README.md                                # docs index
│   ├── data-source.md                           # EDB 站 methodology
│   ├── schema.md                                # metadata schema 詳細
│   ├── legal.md                                 # 法律/版權/PDPO 考慮
│   ├── internet-archive-policy.md               # IA upload 守則
│   ├── faq.md                                   # 教師/研究員 FAQ
│   └── changelog.md
├── tools/
│   ├── scraper.py                               # EDB scraper
│   ├── ia_uploader.py                           # Internet Archive uploader
│   ├── export.py                                # JSON / CSV export
│   ├── validate.py                              # JSON Schema 驗證
│   ├── requirements.txt                         # internetarchive, httpx, bs4, lxml
│   ├── pyproject.toml                           # packaging
│   └── tests/
│       ├── test_scraper.py                      # mock HTML
│       ├── test_parser.py
│       └── fixtures/
│           └── search_result_sample.html
└── .gitignore
```

**GitHub Pages(可選)**:GitHub Pages 對**只 source code + data**嘅 repo 唔需要,但 README + docs/ 嘅 markdown 喺 GitHub 內置 render 已足夠。**唔啟用** GitHub Pages 避免 confusion。

---

## 7. 功能模塊 (Feature Modules)

### 7.1 模塊 A: Scraper(增強版)

- A1-A8(同 v0.1): 沿用 W1 PoC 設計
- **A9 (NEW)**: 增量 scrape — 只 scrape 過去 7 日新增通告
- **A10 (NEW)**: 重 scrape — 偵測 EDB 改檔(SHA-256 mismatch)並重新 mirror
- **A11 (NEW)**: 跨年度 scrape — 預設 scrape 過去 360 日(7 日增量 + 1 次年度補)
- **A12 (NEW)**: 三語 — 繁 / 簡 / 英 全部 scrape(部分通告只有部分語言)
- **A13 (NEW)**: Hash 去重 — 用 SHA-256 避免重複儲存

### 7.2 模塊 B: Internet Archive Uploader

- B1: Item 建立 — `edb-circulars-<year>`(e.g. `edb-circulars-2026`)
- B2: PDF upload + metadata — 透過 `internetarchive` Python library
- B3: Item-level metadata(總體 description, license, rights)
- B4: Per-file metadata(對應 EDB circular_no, date, distribution)
- B5: Retry + backoff(IA server 可能慢)
- B6: Upload log + audit trail

### 7.3 模塊 C: GitHub Repo & Auto-Update

- C1: Repo init + README + LICENSE + CONTRIBUTING
- C2: GitHub Actions 排程 — 每週一 09:00 HKT 自動:
  - C2a: Scrape EDB 過去 7 日
  - C2b: Upload 新 PDF 落 IA
  - C2c: 更新 data/metadata.json + circulars.csv
  - C2d: 自動 commit + push
- C3: PR-based contribution — 用戶可報錯 metadata,自動 issue template
- C4: Release notes via CHANGELOG.md

### 7.4 模塊 D: Documentation(PUBLIC-facing)

- D1: README.md — 講明 project 目的、用法、attribution
- D2: docs/data-source.md — 講清 EDB 站 methodology(scrape 點做、rate limit、retry)
- D3: docs/schema.md — metadata 詳細 schema
- D4: docs/legal.md — 版權 / PDPO / IA safe harbor 完整聲明
- D5: docs/internet-archive-policy.md — IA upload 守則
- D6: docs/faq.md — 教師/研究員 FAQ

### 7.5 模塊 E: 本地工具(可選,二期)

- E1: Local mirror tool — `mirror.sh` 自動 sync IA → 本地 `./pdfs/`
- E2: DuckDB local query(本地 metadata + 全文搜尋)
- E3: Vue 3 UI 顯示 metadata + 開 PDF

---

## 8. 時程 (Timeline v0.2)

### 8.1 階段劃分(8 週完成 MVP,對應方案 A)

| 週次 | 階段 | 主要交付 |
| --- | --- | --- |
| **W1** | ~~Discovery + Scraper PoC~~ | ✅ 已完成(2026-06-15) |
| **W2** | Scraper 完整版 + IA uploader | 過去 360 日 全部 scrape + 全部 PDF 落 IA |
| **W3** | GitHub repo init + Documentation | Public repo, README, LICENSE, schema, FAQ |
| **W4** | GitHub Actions + Auto-update | 每週自動 scrape + commit + IA upload |
| **W5** | Community engagement | GitHub release, edu forum 公告, KOL 教師 outreach |
| **W6** | Schema refinement + Data validation | JSON Schema 強制, PR template, issue template |
| **W7** | Local mirror tool(可選) | `mirror.sh` 自動 sync IA → 本地 |
| **W8** | 文件 + v1.0 release | v1.0 tag, CHANGELOG, blog post |

### 8.2 階段性里程碑

- **M1 (W2 end)**: ✅ 技術上可達 — 過去 360 日全部備份,273 份 PDF 全部落 IA,metadata.json 完整
- **M2 (W3 end)**: ✅ Public repo 公開, 文件齊全, 任何人都可 clone + 用
- **M3 (W4 end)**: ✅ GitHub Actions 自動每週更新, 完全 unattended
- **M4 (W8 end)**: ✅ v1.0 release, 有社區 engagement(stars / PRs)

### 8.3 二期路線圖(W8 之後)

- 二期 1: Vue 3 UI + DuckDB local query
- 二期 2: LLM 主題標註
- 二期 3: 訂閱 / 通知
- 二期 4: 跨部門(KE / FSB)通告整合

---

## 9. 法律 / 合規考量(v0.2 強化)

(同 v0.1 §9,加方案 A 嘅法律框架)

### 9.1 三層法律框架(方案 A)

| 層 | 內容 | 法律依據 |
| --- | --- | --- |
| **EDB 原始 PDF** | 喺 EDB 站 360 日內可訪問 | © 教育局,使用須標明出處 |
| **Internet Archive mirror** | 永久 mirror EDB PDF | IA 嘅 safe harbor + 學術 / archive use case |
| **GitHub metadata** | 公開 metadata(JSON/CSV) | CC0 1.0(放棄 metadata 版權)+ 標明出處 |

### 9.2 為何 metadata 可用 CC0?

- **Metadata 係事實資料**(e.g. 「通告 EDBCM082/2026 喺 2026-06-15 發出,標題 XXX」)— 法律上屬事實(facts)而非創作
- **CC0 適用於資料(databases)**:美國政府 open data 全用 CC0
- **對 EDB 嘅關係**:CC0 唔影響 EDB 本身嘅 © — 仍然要 attribution 出處,我哋只係放棄 metadata 嘅我哋部分版權
- **鼓勵 reuse**:任何人都可商業 / 非商業用 metadata, e.g. 學術研究、商業 dashboard

### 9.3 為何 Internet Archive 對 archive use case 安全?

- **17 U.S.C. § 512 / DMCA safe harbor** — IA 對 archive use case 有明確 legal protection
- **EDB 通告係政府文件**:美國 / 香港政府文件一般可自由 archive,無版權問題
- **Archive use case vs redistribution use case**:Archive = 永久保存供未來查閱(合法);Mass redistribution = 大量再分發(可能有問題)
- **EDB 站無明確禁止 archive**:robots.txt 404, ToS 無 archive clause
- **Attribution 完整**:我哋喺 metadata 入面 explicit 標明 EDB 為 source

### 9.4 PDPO 私隱考慮

- **GitHub 唔 host PDF** — 私隱風險**完全歸零**
- **Internet Archive 係公開 mirror** — 任何人都可 access,但 IA 嘅 archive use case 已有保護
- **EDB 通告可能含 PDPO 敏感資料** — 但呢個係 EDB 站問題,唔係我哋 archive 嘅問題;EDB 自己有責任 redact / 刪除
- **我哋嘅責任**:透明(README 講明), attribution 完整, 不修改原文

### 9.5 免責聲明範本(v0.2 強化)

```
本工具(EDB Circular Vault)為非官方 open data 索引工具。

Metadata 部分:
- 以 CC0 1.0 Universal 釋出,放棄我哋部分版權
- 鼓勵任何 reuse(商業 / 非商業)
- 須保留 attribution 標明出處為教育局

PDF 部分:
- 由 Internet Archive 永久 mirror
- 原始版權屬香港特別行政區教育局(© 教育局版權所有)
- 僅作 archive / 研究用途,非官方 source of truth
- 如發現資料與 EDB 官網不一致,以 EDB 官網為準

工具使用須知:
- 本工具非官方,與教育局無關
- 開發者不對因使用本工具而產生嘅任何損失負責
- Internet Archive link 雖永久但非保證,建議用戶自備本地備份
```

### 9.6 監管動態(同 v0.1)

- PDPO:metadata 唔含個人資料(只有事實),PDF 透過 IA 安全
- 版權條例 § 198:政府公告 free use + attribution
- DMCA safe harbor:IA 對 archive use case 適用

---

## 10. 風險管理 (Risk Register v0.2)

(同 v0.1,加 open data 風險)

| # | 風險 | 影響 | 機率 | 緩解策略 | 負責人 |
| --- | --- | --- | --- | --- | --- |
| R1 | ASP.NET WebForms scraper 太複雜 | 高 | 中 | W1 PoC 已驗證,low risk | 開發者 |
| R2 | EDB 改版,scraper 失效 | 高 | 中 | scraper 模塊化,加 unit test,每週 monitor | 開發者 |
| R3 | Internet Archive upload 慢 / 失敗 | 中 | 中 | 大量 file 用 batch upload,retry + backoff | 開發者 |
| R4 | Internet Archive link 失效 | 高 | 極低 | IA 過往 25 年 link stability 高,monitor 季度檢查 | 開發者 |
| R5 | EDB issue takedown 投訴 | 中 | 低 | 我哋 host 嘅只係 metadata(legal 清晰);IA 嘅 mirror 屬 archive use case | 開發者 |
| R6 | PDPO 投訴(由 EDB / 第三方) | 中 | 低 | GitHub 無 PDF,責任喺 EDB 自己 | 開發者 |
| R7 | 社區唔採用(star / fork 少) | 中 | 中 | W5 community engagement, KOL outreach | 開發者 |
| R8 | GitHub Actions quota 耗盡 | 低 | 極低 | Free quota 2,000 min/month,本 project < 50 min/month | 開發者 |
| R9 | PDF parsing 失敗(掃描式 PDF) | 中 | 中 | pytesseract OCR 兜底;若失敗 metadata 仍記錄 | 開發者 |
| R10 | LLM 主題標註 quality 低 | 中 | 中 | 字典法做 MVP,LLM 留二期 | 開發者 |
| R11 | 開發者失去動力 | 高 | 高 | M1-M4 硬 milestone,每 2 週 self-review | 開發者 |
| R12 | (NEW) PDF size > IA limit | 低 | 極低 | IA 無 size limit,確認過 | 開發者 |
| R13 | (NEW) IA 對批量 upload 限流 | 中 | 中 | 限 1 file/5sec,retry + backoff | 開發者 |

---

## 11. MVP 定義 (Minimum Viable Product)

### 11.1 MVP 範圍(W2-W4 完成)

**目標**:證明方案 A 嘅 open data + IA mirror 概念 work。

**包含**:
- ✅ W1: Scraper PoC(已完成)
- ⏳ W2: Scraper 增強版 + IA uploader — 過去 360 日全部 scrape + 全部 PDF 落 IA
- ⏳ W3: GitHub public repo init + README + LICENSE + 完整 docs/
- ⏳ W4: GitHub Actions 自動每週 scrape + commit + IA upload

**不包含**(留俾 W5+ 或二期):
- ❌ Vue 3 UI
- ❌ DuckDB local query
- ❌ LLM 主題標註
- ❌ 訂閱 / 通知
- ❌ 本地 mirror tool(可選二期)

### 11.2 MVP 成功標準

| 指標 | 目標值 |
| --- | --- |
| Scrape 成功率 | ≥ 95% |
| PDF download 成功率 | ≥ 95% |
| IA upload 成功率 | ≥ 90%(IA server 慢,預期有 retry) |
| GitHub repo public + 完整文件 | 100% |
| GitHub Actions auto-update work | 100% |
| archive.org link 永久 work | 100%(post-W4 verify) |
| README 點擊 → 5 分鐘內 clone + 用 metadata | 100% |

---

## 12. 開放問題 / 下一步(同 v0.1,加 defaults)

### 12.1 須 PM 確認(已部分答)

| # | 問題 | 狀態 | 推薦 / 默認 |
|---|---|---|---|
| 1 | 工具命名 | PENDING | 推薦:**"EDB Circular Vault"** (中:「教育通備」) |
| 2 | 發佈渠道 | ✅ **方案 A 已隱含答 = Public GitHub + Internet Archive** | — |
| 3 | 商業化 | PENDING | 推薦:**先免費**(open data spirit),二期再考慮 SaaS |
| 4 | 開發優先級 | PENDING | 推薦:**8 週 MVP + 2 週 buffer** |
| 5 | 用戶訪問時機 | PENDING | 推薦:**W5 community engagement**(KOL 教師 + 教育 forum) |

### 12.2 W2 即將開工嘅具體 task(等你 "go")

**W2 task breakdown**:

1. **T1: Schema finalize** (1-2 小時)
   - 落實 §6.4 嘅 SQL + JSON schema
   - 寫 JSON Schema 定義 file

2. **T2: Scraper enhance** (3-4 小時)
   - 加 A9-A13(增量,重 scrape,三語, hash 去重)
   - 完整 scrape 過去 360 日(估 700+ 份,1-2 小時 runtime)

3. **T3: IA uploader** (3-4 小時)
   - 用 `internetarchive` library
   - Item = `edb-circulars-<year>`
   - Per-file metadata
   - Retry + backoff

4. **T4: 第一次 push** (1-2 小時)
   - 跑完整 scrape + upload
   - 產出 metadata.json + circulars.csv
   - 驗證 archive.org link work

5. **T5: GitHub repo init** (2-3 小時,W3 開工)
   - 建 public repo
   - 寫 README + LICENSE + CONTRIBUTING
   - docs/ 全部章節
   - 第一次 commit

**W2 工時估**:10-15 小時(1 個 weekend 完成)

### 12.3 PM 嘅 trigger 詞

開工 = 一句 **"go"** / **"開工"** / **"開 W2"**。我即刻按 T1 → T5 順序執行,完成一個 task 報 status, 完成 W2 報 milestone M1。

---

## 13. 附錄

### 13.1 EDB 通告站 URL 結構(同 v0.1)

| 用途 | URL |
| --- | --- |
| 列表(繁中,過去 360 日) | `https://applications.edb.gov.hk/circular/circular.aspx?langno=2&circular_distribution=&search_type=1&issueDay=360` |
| 詳情頁 | `https://applications.edb.gov.hk/circular/circular_memo.aspx?langno=2&circular_id=<id>` |
| 通告 PDF(直接 URL) | `https://applications.edb.gov.hk/circular/upload/EDBC(M)/XXX[C|E|S].pdf` |

### 13.2 通告編號格式(同 v0.1)

`EDBC` = 通告 / `EDBCM` = 通函,後 5 位係流水號(年份+序號)

### 13.3 參考資源

- EDB 通告主頁: https://www.edb.gov.hk/tc/about-edb/forms-and-circulars/index.html
- 政府版權聲明: https://www.gov.hk/tc/about/copyright/
- PDPO: https://www.pcpd.org.hk/tc_chi/data_privacy_law/ordinance_at_a_Glance/ordinance.html
- Internet Archive 上載: https://archive.org/upload
- Internet Archive Python library: https://pypi.org/project/internetarchive/
- GitHub Free 計劃: https://github.com/pricing
- CC0 1.0 Universal: https://creativecommons.org/publicdomain/zero/1.0/
- W1 PoC artifacts: `/Users/apple/.mavis/sessions/mvs_b78623d5503c46fe86d75edf7cf816d4/workspace/poc_output/`

### 13.4 文件版本控制

| 版本 | 日期 | 修改者 | 修改 |
| --- | --- | --- | --- |
| v0.1 | 2026-06-15 | Mavis (PM) | 初稿,14 章節 |
| v0.2 | 2026-06-16 | Mavis (PM) | **方案 A 落地** — Public metadata + Internet Archive mirror。新增 §15 / §16 / §17,更新 §1 / §4 / §6.4 / §6.5 / §8 / §9 / §11。隱含答咗 PM 問題 #2。 |

---

## 14. PM 嘅一句話總結(更新)

呢個項目嘅核心價值**唔再係「為教育界做工具」,而係「為教育界做 open data contribution」**。從私有工具轉向公共 mirror,係對 EDB 通告長遠可訪問性嘅最大貢獻。

技術挑戰中等(scraper 已驗證,IA uploader 標準 library),法律風險低(CC0 metadata + IA safe harbor),市場窗口存在(政府文件永久 archive 嘅需求)。**最大失敗風險仍係開發者動力**——M1 (W2) 同 M2 (W3) 嘅硬 milestone 至關重要。

**先求有,再求好。等 PM 一句 "go" 即開 W2。**

---

## 15. Open Data 路線圖(方案 A 詳述)(NEW)

### 15.1 為何方案 A 係最佳?

(已喺 §1 同 §6.3 詳述,呢度做 summary)

| 維度 | 方案 A(Public metadata + IA) | 方案 B(GitHub LFS PDF) | 方案 C(Public PDF + redaction) |
|---|---|---|---|
| 私隱風險 | **0**(GitHub 無 PDF) | 高(永久 host) | 中(redaction 不完美) |
| 法律風險 | **低**(CC0 metadata + IA safe harbor) | 中(mass redistribution) | 中 |
| 解決 360 日清除 | **✅**(IA 永久) | ✅(但 private 不算 open) | ✅ |
| 開放程度 | **高**(metadata open) | 中(LFS 仍要 GitHub account) | 高 |
| 成本 | **$0** | $0 | $0 + 開發 redaction |
| 對 EDB 友好 | **高**(只 metadata) | 低(mass host) | 中 |
| 社區價值 | **高**(others 可 contribute) | 低(private) | 中 |
| 維護負擔 | **低**(GitHub Actions auto) | 低 | 高(redaction pipeline) |

### 15.2 社區 engagement 計劃

**W5 嘅 KOL outreach 目標**:
- 5 個 KOL 教師(教師 Facebook group / Telegram 群組)
- 3 個教育界 NGO(例如教協、社工)
- 2 個政策研究機構(e.g. 教大、教育政策學者)
- 1 個 Reddit / Quora post(open data 社群)
- 1 個 GitHub 內推(Hacker News / Show HN)

**預期 outcome**:
- ≥ 10 GitHub stars
- ≥ 3 external PRs(報錯 metadata,加 subject 分類,translate docs)
- ≥ 1 教育媒體報導(教報 / 教協通訊)
- ≥ 1 academic citation

### 15.3 中長期願景

- **v1.0 (W8)**: Public repo, auto-update, full docs
- **v1.1 (W12)**: Subject 分類(LLM 標註), 全文搜尋(Vue 3 UI)
- **v2.0 (Q4 2026)**: 跨部門(KE / FSB / EMSD)通告整合
- **v3.0 (2027)**: SaaS 版本(教育機構訂閱, 本地優先 cloud sync)

---

## 16. GitHub Repo Structure — 詳述(NEW)

(已喺 §6.5 展示,呢度加補充)

### 16.1 README.md 大綱(繁中)

```markdown
# EDB Circular Vault — 教育局通告 Open Data 索引

> 為香港教育界提供永久可訪問嘅 EDB 通告 metadata 索引

## 點解有呢個 project?
教育局通告站 360 日後清除通告,教師/行政/政策研究員需要永久 mirror。
本工具透過 GitHub (metadata) + Internet Archive (PDF) 雙軌,
將 EDB 通告永久 archive 供公眾使用。

## 點樣用?
- **查通告**:見 `data/circulars.csv` 或 [GitHub 搜尋](...)
- **拎 PDF**:click 任何 circular 嘅 `archive_url`(Internet Archive 永久 mirror)
- **本地 mirror**:見 `tools/mirror.sh`(下載 PDF 到本地 `./pdfs/`)

## 點樣 contribute?
- 報錯 metadata:見 [ISSUE_TEMPLATE/data_correction.md](...)
- 翻譯 docs:PR 到 `docs/`
- 改良 scraper:PR 到 `tools/scraper.py`

## License
- **Metadata** (data/metadata.json, data/circulars.csv): [CC0 1.0](https://creativecommons.org/publicdomain/zero/1.0/)
- **Tools** (tools/*, docs/*): [MIT](https://opensource.org/licenses/MIT)
- **PDF**: © 教育局,僅作 archive / 研究用途

## 資料來源
[香港特別行政區教育局](https://www.edb.gov.hk/)
[Internet Archive](https://archive.org/)

## 免責聲明
本工具非官方,與教育局無關。
```

### 16.2 LICENSE 雙 license

- `LICENSE-CC0` 適用於 `data/` 入面所有 metadata
- `LICENSE-MIT` 適用於 `tools/` 同 `docs/`

### 16.3 docs/ 詳細章節

| File | 內容 |
|---|---|
| `README.md` | docs index |
| `data-source.md` | EDB 站 methodology(scrape 點做, rate limit, retry, 過去 limitations) |
| `schema.md` | metadata schema 詳細(每個 field 解釋 + example) |
| `legal.md` | 版權 / PDPO / IA safe harbor 完整聲明(同 §9 加長版) |
| `internet-archive-policy.md` | IA upload 守則(item naming, metadata, retry) |
| `faq.md` | 教師 / 研究員 / 開發者 FAQ |

---

## 17. Internet Archive Upload 範本(NEW)

### 17.1 Python 範本(用 `internetarchive` library)

```python
import internetarchive as ia

ITEM_NAME = "edb-circulars-2026"

# 1. Login(透過環境變數)
#   IA_ACCESS_KEY, IA_SECRET_KEY 喺 ~/.ia_config 或 env

# 2. Get or create item
item = ia.get_item(ITEM_NAME)
if not item.exists:
    item.modify_metadata(
        metadata=dict(
            title="EDB Circulars 2026",
            creator="Education Bureau, HKSAR Government",
            publisher="Education Bureau, HKSAR Government",
            date="2026",
            language="zh-HK",
            licenseurl="https://creativecommons.org/publicdomain/zero/1.0/",
            rights="Metadata: CC0. PDF: © Education Bureau, archive use only.",
            description="Mirror of Education Bureau circulars issued in 2026, archived from https://applications.edb.gov.hk/circular/. See project: https://github.com/USER/edb-circular-vault",
            subject=["Education", "Hong Kong", "EDB", "Circular", "Open Data"],
            collection="opensource",
        )
    )

# 3. Upload PDF
for pdf_path, meta in pdf_list:
    response = item.upload_file(
        pdf_path,
        metadata=dict(
            title=meta["title"],
            date=meta["issue_date"],
            description=meta["summary"][:500] if meta["summary"] else "",
            subject=meta["distribution"],
            language=meta["lang"],
            source_url=meta["source_url"],
            circular_no=meta["circular_no"],
        ),
        queue_derive=True,  # 自動 generate derivatives
        verify=True,         # 上傳後 verify
    )
    print(f"Uploaded {pdf_path}: {response.status_code}")

# 4. Get archive URL
for file in item.files():
    print(f"https://archive.org/download/{ITEM_NAME}/{file['name']}")
```

### 17.2 IA item structure(預期)

```
edb-circulars-2026/
├── EDBCM26082C.pdf
├── EDBCM26077C.pdf
├── EDBC26010C.pdf
├── EDBCM26105C.pdf
├── EDBCM26089C.pdf
├── ... (估 700+ 份)
├── edb-circulars-2026_files.xml  (auto-generated)
└── edb-circulars-2026_meta.xml   (auto-generated)
```

### 17.3 IA 上傳 rate limit & best practices

- **Rate limit**: 1 request/second(建議)
- **Retry**: 5 次, exponential backoff (5, 15, 30, 60, 120 sec)
- **Batch upload**: 用 `internetarchive` library 嘅 batch API,內部有 queue
- **Verification**: upload 後 check `item.exists` + `item.file_metadata()`
- **Backup**: 多個 IA item(per-year)分拆,避免單一 item 太大

---

## 18. PM 嘅 next step 摘要

**等你一句 "go" 即開 W2**:

1. T1: Schema finalize (1-2 hr)
2. T2: Scraper enhance (3-4 hr)
3. T3: IA uploader (3-4 hr)
4. T4: 第一次 push — 完整 scrape + upload (1-2 hr, runtime 1-2 hr)
5. T5: GitHub repo init(W3 開工)

**Trigger 詞**:**"go"** / **"開工"** / **"開 W2"** / **"start"**

我會喺 W2 開工後,每完成一個 T 報 status,完成 M1 報 milestone。

**仲有 4 條 PM 問題未答**(§12.1):#1 命名 / #3 商業化 / #4 開發優先級 / #5 用戶訪問。如果你對 defaults OK,直接 "go" 我就默認推進;想改邊條,直接講。

---

**Document end.**
