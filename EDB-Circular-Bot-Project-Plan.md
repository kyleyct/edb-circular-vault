# 教育局通告備份與分析 Bot — 項目計劃書

> **文件性質**: 項目經理(PM)視角嘅專案計劃書
> **對象**: 開發者本人(用戶)、未來潛在協作者
> **撰寫日期**: 2026-06-15 (v0.1) / 2026-06-16 (v0.2)
> **版本**: v0.2 — **2026-06-16 更新(方案 A 落地,見 §15)**
> **語言**: 香港繁體書面語
>
> **⚠️ 本文件已 superseded — 請參閱 v0.2:** `EDB-Circular-Bot-Project-Plan-v0.2.md`
> v0.1 保留作歷史紀錄, § 4.1 / 6.4 / 6.5 / 8 / 9 / 11 等已過時。

---

## 1. 項目摘要 (Executive Summary)

教育局通告(EDB Circular)係香港學校教師與行政人員日常運作嘅「搵食工具」:由收生安排、課程更新、教師培訓、學校行政指引,以至突發事項(停課、颱風、防疫),全部經此渠道發佈。

問題:教育局(`applications.edb.gov.hk/circular/`)只保留**過去 360 日**(一年)嘅通告,過期就清除。教師手上嘅 PDF 又散落各人手機、email、自家電腦,3 個月後想搵返一份政策更新,往往要撲空。

本項目嘅目標:**建立一個本地優先嘅備份與分析工具**,自動抓取、永久保存、分類索引所有 EDB 通告,並為教師/行政人員提供搜尋、訂閱、提醒功能。

關鍵設計原則:
1. **100% 本地處理**:所有備份、分析、搜尋喺用戶電腦進行,無雲端,無追蹤,符合學校敏感資料嘅私隱要求。
2. **政府文件可自由使用**:香港政府公告一般容許市民使用及翻印(需標明出處),但本工具須明確標示「非官方 mirror,以 EDB 為準」以避開責任風險。
3. **無外部 API**:EDB 通告頁係傳統 ASP.NET WebForms,無 REST API,需要自建 scraper。

---

## 2. 問題陳述 (Problem Statement)

### 2.1 痛點 (Pain Points)

| 痛點 | 受影響角色 | 影響程度 |
| --- | --- | --- |
| 通告過期被清除 | 教師、校長、行政主任 | 高 — 直接影響日常工作 |
| PDF 附件散落各方 | 全校教職員 | 中 — 重複下載、版本混亂 |
| 搜尋介面唔友善 | 新入職教師 | 中 — EDB 官方搜尋體驗差 |
| 跨年份比較困難 | 政策研究員、科主任 | 高 — 無法睇 5 年走勢 |
| 訂閱/提醒機制欠奉 | 校長、行政 | 中 — 依賴 email forward |
| 簡體中文版(langno=3)亦同步運作 | 跨境教師、內地新來港 | 低 — 雙語對照需求 |

### 2.2 現有方案嘅不足

- **官方 EDB 通告頁**:只保留 360 日,搜尋只限當下一年,無 API,無 RSS。
- **第三方通告轉發群組(WhatsApp/Telegram)**:只流動少量,非歸檔,無搜尋。
- **教育界博客/KOL 整理**:零散、唔齊全,作者停更就消失。
- **立法會文件系統**:只覆蓋立法會相關通告,非 EDB 全部。
- **Google 搜尋**:可見性低(EDB 站內 SEO 弱),且只見快照,有時連標題都搜唔到。

### 2.3 機會窗口 (Why Now)

- 過去幾年 EDB 通告量穩步上升(國安教育、AI 教學、特殊教育等新範疇),對工具需求增加。
- 香港教師/行政人員對「本地工具」接受度高(已有教師私 telegram 群、自建 Excel 表嘅習慣)。
- DuckDB-WASM 等技術成熟,本地優先嘅資料工具技術門檻已大幅降低。

---

## 3. 目標與成功指標 (Goals & KPIs)

### 3.1 業務目標 (Business Goals)

| 目標 | 衡量指標 | 目標值 (12 個月) |
| --- | --- | --- |
| G1: 備份完整性 | 已備份通告 / EDB 同期通告 | ≥ 99% |
| G2: 跨年存取 | 用戶可查詢 5 年前嘅通告 | 5 年資料庫可運作 |
| G3: 搜尋準確度 | 用戶搜尋「公民教育」相關通告,前 5 結果命中率 | ≥ 90% |
| G4: 隱私合規 | 工具零雲端依賴,本地處理 | 100% 本地(可離線) |

### 3.2 用戶目標 (User Goals)

- **U1**(教師):「我下學期教公民科,想睇晒近 3 年 EDB 點樣更新公民教育。」
- **U2**(行政主任):「有校長問我 2023 年 9 月嗰份關於學校維修嘅通告,EDB 已經清除咗,你有冇?」
- **U3**(校長):「我想訂閱『學校行政』+『小學』嘅通告,出咗就通知我。」
- **U4**(政策研究員):「我想分析 5 年內 EDB 通告嘅主題分佈。」

### 3.3 技術目標 (Technical Goals)

- 每日自動備份新通告,失敗有 retry + 通知。
- 支援離線操作(本地資料庫),無需連網。
- 啟動時間 ≤ 3 秒(本地 DuckDB-WASM)。
- 搜尋響應時間 ≤ 200ms(本地查詢)。

### 3.4 非目標 (Non-Goals)

- ❌ 取代 EDB 官方搜尋(我哋係 mirror/backup,非 source of truth)。
- ❌ 即時通訊、評論、社交功能。
- ❌ 多用戶協作(本階段單機單用戶)。
- ❌ 行動 App(本階段聚焦 desktop / web 工具)。
- ❌ 通告「分析」後嘅政策解讀(呢個係 AI 範疇,留俾二期)。

---

## 4. 範圍 (Scope)

### 4.1 In Scope(本期做)

| 模塊 | 描述 |
| --- | --- |
| 自動備份 | 每日/手動 trigger,備份當日 EDB 通告 metadata + PDF 附件 |
| 本地資料庫 | DuckDB 儲存 metadata(編號、日期、標題、分發組別、主題、PDF 路徑) |
| 全文搜尋 | 標題 + PDF 內容(OCR/extracted text) |
| 分類與標籤 | 按分發組別(學前/小學/中學/特殊/專上)、時期、語言過濾 |
| 訂閱 | 用戶自訂關鍵字 + 分發組別,新通告出現時本地通知 |
| 匯出 | 個別通告可下載原 PDF + metadata JSON |
| 雙語 | 同時備份繁體(langno=2)及簡體(langno=3)版本 |
| 跨年存取 | 預期支援 5 年+ 資料量 |

### 4.2 Out of Scope(本期不做,留俾二期或不做)

- ❌ 通告內容嘅 AI 摘要/政策解讀
- ❌ 通告之間嘅關聯性分析
- ❌ 學校內部流通(校園版)
- ❌ SaaS/雲端服務
- ❌ 多用戶帳號系統
- ❌ 通告真實性驗證(我哋假定 EDB 嘅資料正確,只係 mirror)
- ❌ 其他政府部門嘅通告(KE, FSB, EMSD 等)

---

## 5. 利益相關者 (Stakeholders)

| 角色 | 對工具嘅期望 | 影響 / 介入度 |
| --- | --- | --- |
| **教師**(主要用戶) | 易用、搜尋快、唔使學新嘢 | 高 — 影響採用率 |
| **學校行政主任**(主要用戶) | 齊全、可靠、方便引用過往通告 | 高 — 影響核心價值 |
| **校長**(次要用戶) | 訂閱、提醒 | 中 — 影響黏性 |
| **科主任 / 統籌**(次要用戶) | 主題分類、跨年比較 | 中 — 影響深度採用 |
| **教育界 NGO / 政策研究員**(邊緣用戶) | 完整資料、export CSV/JSON | 低 — 但係品牌建立嘅關鍵 |
| **教育局 EDB**(被動 stakeholder) | 無要求、無反對 | 低 — 但係版權與禮儀關鍵 |
| **開發者(用戶本人)** | 個人興趣 + 商業潛力 | 100% — 唯一決策者 |

### 5.1 用戶訪談對象建議

開發者應喺 MVP 之前訪問至少 5 位潛在用戶:
- 2 位教師(中學/小學各 1)
- 1 位行政主任
- 1 位校長
- 1 位科主任或政策研究員

問題清單(PM 提示):
- 你通常點搵 EDB 通告?(Google? EDB 官網? Telegram?)
- 試過搵唔到一份已知存在嘅通告嗎?
- 如果有一個本地搜尋器,你會唔會每週用?
- 你願意用一啲(15-30 分鐘)時間學新工具嗎?

---

## 6. 技術架構推薦 (Technical Architecture)

### 6.1 整體架構圖

```
┌──────────────────────────────────────────────────────────────┐
│                本地電腦 (User's Mac/PC)                       │
│                                                              │
│  ┌─────────────┐    ┌──────────────┐    ┌───────────────┐   │
│  │  Scraper    │───▶│  DuckDB      │◀───│  Frontend     │   │
│  │  (Python)   │    │  (本地檔案)  │    │  (Vue 3 SPA)  │   │
│  └──────▲──────┘    └──────────────┘    └───────────────┘   │
│         │                                       │            │
│         │           ┌──────────────┐           │            │
│         └──────────▶│  PDF Storage │◀──────────┘            │
│                     │  (./pdfs/)   │     點擊下載              │
│                     └──────────────┘                          │
│                                                              │
│  排程:    cron / launchd (macOS) / Task Scheduler (Win)      │
│  通知:    本地桌面通知 + log file                            │
└──────────────────────────────────────────────────────────────┘
                              ▲
                              │ HTTPS
                              │ (限速 1 req/s)
                              │
                  ┌───────────┴────────────┐
                  │  EDB 通告站             │
                  │  (WebForms, 無 API)     │
                  └────────────────────────┘
```

### 6.2 技術棧 (Tech Stack)

| 層 | 技術 | 理由 |
| --- | --- | --- |
| Scraper | Python 3.12 + httpx + BeautifulSoup4 + lxml | httpx 支援 async,BS4 處理 HTML,簡單可靠 |
| WebForm 處理 | 自寫 `aspnet_form.py`(處理 VIEWSTATE/EVENTVALIDATION) | WebForms scraper 無 off-the-shelf 方案,自寫可控 |
| 排程 | cron / launchd (macOS) / Task Scheduler (Windows) | 跟「本地優先」原則,無需外部服務 |
| 資料庫 | DuckDB-WASM(喺 browser 入面) | 跟 W1 hk-open-school 嘅技術選型,本地檔案式,效能高 |
| Backend 數據橋 | Python export JSON/Parquet → frontend 讀 | 簡單,無需 server |
| Frontend | Vue 3 + Vite + TypeScript | 跟 W1,香港開發者熟悉 |
| 搜尋 | DuckDB FTS extension(全文搜尋) | 原生支援中文分詞(tokenize),無需外部索引 |
| PDF 解析 | pdfplumber + pytesseract (for scanned PDF) | EDB 通告 PDF 部分係純文字,部分係掃描,雙軌處理 |
| 版本控制 | Git + GitHub (private repo) | 跟用戶私隱取向 |
| 文件 | Markdown + MkDocs | 簡單靜態文件站 |

### 6.3 關鍵技術決策

**D1: 為何用 DuckDB-WASM 而非 SQLite?**
- DuckDB 原生支援複雜查詢(SQL analytic queries),適合分析「5 年通告分佈」呢類場景
- DuckDB FTS extension 對中文支援較好
- W1 hk-open-school 已有先例,技術風險低
- 缺點:啟動時間略長(SQLite 即時啟動),但對於本地工具可接受

**D2: 為何 Vue 3 而非 React?**
- 跟 W1 一致,降低維護成本
- 用戶熟悉 Vue
- Composition API 對 TypeScript 友好

**D3: 為何 Python scraper 而非 Node.js?**
- Python 處理 HTML / PDF / NLP 嘅 library 較成熟
- httpx + asyncio 效能足夠
- 用戶可能已熟悉 Python

**D4: 為何本地排程而非要雲端?**
- 用戶私隱取向(敏感)
- 學校 PDF 唔應該出 internet
- 月費 = 0
- 缺點:用戶要裝排程,教育門檻略高 — 用 `start-demo.sh` 一鍵安裝緩解

**D5: PDF 鏡像策略**
- 唔抽取 PDF 入資料庫(只儲 metadata + 全文)
- 原 PDF 留喺 `./pdfs/<circular_id>.pdf`
- 用戶可離線時照樣開 PDF

### 6.4 數據模型 (Data Model)

```sql
-- 主要表格
CREATE TABLE circular (
  id              VARCHAR(20) PRIMARY KEY,    -- EDB circular number, e.g. "EDB(CM)123/2024"
  issue_date      DATE NOT NULL,              -- 發出日期
  title           TEXT NOT NULL,              -- 通告標題
  distribution    TEXT[],                     -- 分發組別, e.g. ['Kindergarten', 'Primary']
  subject         TEXT,                       -- 主題 (e.g. "公民教育", "學校行政")
  lang            VARCHAR(2),                 -- 'zh-HK' (繁中) / 'zh-CN' (簡中)
  pdf_path        TEXT,                       -- ./pdfs/EDB(CM)123/2024_zh-HK.pdf
  text_path       TEXT,                       -- ./text/EDB(CM)123/2024_zh-HK.txt
  scraped_at      TIMESTAMP,                  -- 抓取時間
  source_url      TEXT,                       -- 原始 URL
  content_hash    VARCHAR(64),                -- SHA-256 of PDF, 用嚟偵測 EDB 改檔
  superseded_by   VARCHAR(20),                -- 取代此通告嘅新版本
  remarks         TEXT                        -- 開發者備註
);

-- 全文搜尋索引
CREATE INDEX circular_fts ON circular USING FTS (title, subject, text_path);

-- 訂閱記錄
CREATE TABLE subscription (
  id              INTEGER PRIMARY KEY,
  keywords        TEXT[],
  distribution    TEXT[],
  notify_method   VARCHAR(20),                -- 'desktop' / 'log' / 'email' (email 二期)
  created_at      TIMESTAMP,
  last_matched    TIMESTAMP
);

-- 抓取日誌
CREATE TABLE scrape_log (
  id              INTEGER PRIMARY KEY,
  run_at          TIMESTAMP,
  circulars_new   INTEGER,
  circulars_updated INTEGER,
  errors          TEXT,
  duration_sec    REAL
);
```

---

## 7. 功能模塊 (Feature Modules)

### 7.1 模塊 A: Scraper(備份)

**責任**: 自動/手動抓取 EDB 通告,儲存到本地。

**核心功能**:
- A1: 抓取列表頁(`circular.aspx`),支援分發組別、時期、語言 filter
- A2: 處理 ASP.NET WebForm 表單(POST + VIEWSTATE)
- A3: 解析列表,拎到 circular_id,進入 detail 頁
- A4: 下載 PDF 附件
- A5: 提取 PDF 文字(供全文搜尋)
- A6: 儲存 metadata 到 DuckDB
- A7: 速率限制(≤ 1 req/sec)同禮貌 User-Agent
- A8: 錯誤重試(exponential backoff,最多 3 次)
- A9: 抓取日誌(可審計)

**A1 列表抓取嘅關鍵 challenge**:
- URL filter:`langno=2`(繁中)/ `langno=3`(簡中) / `circular_distribution=ALL` / `issueDay=360`(過去一年) / `search_type=1`(簡單搜尋)
- 表單 filter: 仲有 DropDownList/ListBox 類別(分發組別),要靠 POST
- 翻頁: WebForm 用 `__VIEWSTATE` + `__EVENTTARGET` 控制,需要模擬瀏覽器行為

**A3 Detail 頁解析**:
- 從列表頁拎到 detail URL(可能係 `circular_memo.aspx?circular_id=...`)
- Detail 頁含 PDF 下載連結 + 通告 metadata
- 部分通告只有 HTML,無 PDF(要 fallback)

**A4 PDF 下載**:
- 從 detail 頁搵 PDF href
- 用 httpx 下載,儲存到 `./pdfs/<circular_id>_<lang>.pdf`
- 用 content hash(SHA-256)偵測 EDB 改檔

### 7.2 模塊 B: Analyzer(分析/分類)

**責任**: 為通告加上 metadata,方便搜尋/過濾。

**核心功能**:
- B1: 自動分類(按分發組別、時期、語言 — 直接從 EDB 拎)
- B2: 主題提取(用 keyword extraction 或 LLM 標註 — 可選)
- B3: 跨年比較(例如「過去 5 年『國安教育』通告數量」)
- B4: 通告之間關聯(例如「通告 A 取代通告 B」)

**B2 主題提取嘅選擇**:
- 簡單: 用 keyword dictionary(教育界常見主題:公民教育、STEM、特殊教育、學校行政、課程發展、教師培訓、評核、訓輔、家校合作、國安教育……)
- 進階: 用 LLM(本地或 API)自動標註 — 但成本/私隱要權衡
- 建議: 字典法做 MVP,LLM 留俾二期

### 7.3 模塊 C: Search(搜尋/過濾)

**責任**: 用戶界面,提供快速搜尋。

**核心功能**:
- C1: 全文搜尋(標題 + 內容)
- C2: 過濾:分發組別、時期、語言、主題
- C3: 排序:按日期、相關度
- C4: 分頁(每年 200-500 份,5 年有過千份,需要分頁)
- C5: 結果預覽(title + 摘要 + metadata)
- C6: 點擊結果 → 開 PDF / 顯示 metadata

**C1 全文搜尋**:
- DuckDB FTS extension
- 中文分詞: jieba (Python) / 預處理 tokenize 後存
- 搜尋 example: 「公民教育」 → 5 秒內返回前 50 結果

### 7.4 模塊 D: Subscription(訂閱/通知)

**責任**: 用戶訂閱特定條件嘅通告,有新嘅時本地通知。

**核心功能**:
- D1: 訂閱管理(CRUD)
- D2: 配對引擎:每次抓取後,新通告與訂閱比對
- D3: 本地通知(macOS Notification Center / Windows Toast)
- D4: Log file 記錄所有 matched 通告
- D5: (二期) Email 通知

### 7.5 模塊 E: Export(匯出)

**責任**: 用戶可下載/匯出資料。

**核心功能**:
- E1: 個別 PDF 下載(zip 包含 PDF + metadata JSON)
- E2: 搜尋結果匯出(CSV / JSON)
- E3: 整年通告匯出(zip 全部 PDF)
- E4: 訂閱 config 匯出/匯入(JSON)

---

## 8. 時程 (Timeline)

### 8.1 階段劃分(預計 8 週完成 MVP)

| 週次 | 階段 | 主要交付 |
| --- | --- | --- |
| **W1** | Discovery & Scraper PoC | 用 Python 抓取 5 份樣本通告(PDF + metadata)驗證技術可行 |
| **W2** | Scraper 完整版 | 全自動抓過去 360 日所有通告,離線跑得到 |
| **W3** | 資料庫 + 基本 UI | DuckDB schema 建立,Vue 3 UI 顯示通告列表(無搜尋) |
| **W4** | 全文搜尋 | DuckDB FTS + 搜尋介面 |
| **W5** | 分類 + 過濾 | 過濾器、排序、分頁 |
| **W6** | 訂閱 + 通知 | 本地通知,簡單 subscription 管理 |
| **W7** | 匯出 + 雙語 | PDF / CSV / JSON 匯出,繁簡對照 |
| **W8** | 文件 + 本地 demo | README、start-demo.sh、用戶手冊,完成 alpha |

### 8.2 階段性里程碑

- **M1 (W2 end)**: Scraper 跑得通,可以備份一年嘅通告。
- **M2 (W4 end)**: 用戶可以喺本地搜尋 5 年嘅通告。
- **M3 (W6 end)**: 用戶可以訂閱,新通告出現有本地通知。
- **M4 (W8 end)**: Alpha 完成,可以搵 5-10 個真實用戶試用。

### 8.3 二期路線圖(2026 H2 之後)

- B-Phase 1: LLM 主題標註(本地 Ollama)
- B-Phase 2: 多用戶(local network 分享)
- B-Phase 3: AI 摘要(通告內容生成 TL;DR)
- B-Phase 4: 通告關聯性分析(自動偵測取代關係)
- B-Phase 5: 跨部門(KE / FSB / EMSD)通告整合

---

## 9. 法律 / 合規考量 (Legal & Compliance)

呢個係**最重要嘅 non-functional requirement**之一。PM 必須喺 MVP 上線前搞清楚。

### 9.1 香港政府公告嘅版權

**結論**: 香港政府鼓勵市民使用政府公告作非商業用途,但有標明出處嘅責任。

**法律依據**:
- 香港《版權條例》第 198 章
- 政府公告一般屬「政府版權」(Crown Copyright),可自由使用、翻印、轉載,但**須標明「資料來源:教育局」**等字眼
- 非商業、學術、討論用途一般無問題
- 商業轉售(如賣訂閱服務)需要小心

**本工具嘅使用方式**:
- 純備份 + 本地搜尋 — **屬合理使用範圍**
- 唔賣訂閱、唔商業化 — **安全**
- 唯一要求: 工具 UI 明顯位置標明「資料來源:教育局」,免責聲明講明「本工具非官方,以 EDB 為準」

### 9.2 Scraping 禮儀

- EDB 通告站**無 robots.txt**(已確認),理論上可以爬但要自律
- **速率限制**: ≤ 1 request / second(以單機計),避免對 EDB 站造成負擔
- **User-Agent**: 用有意義嘅 UA,例如 `EDB-Circular-Backup-Tool/0.1 (+https://example.com)`
- **高峰期避讓**: 朝早 9 點前 / 夜晚 10 點後(學校用戶最少嘅時段)
- **錯誤處理**: EDB 站 5xx 時,長 backoff 30-60 分鐘
- **無身份偽裝**: 用真實 User-Agent,唔用 fake cookies 扮 browser

### 9.3 私隱考量(用戶角度)

- 本工具**100% 本地**,無雲端,無追蹤,符合學校敏感資料要求
- 唔收集用戶行為、唔收集通告以外嘅資料
- PDF 儲存喺用戶自選位置(預設 `./pdfs/`,可改到 USB / 加密 drive)
- README 明確標示「無公開 Demo」(跟用戶 W1 嘅偏好)

### 9.4 免責聲明範本(供 MVP 採用)

```
本工具為非官方備份工具,所有通告版權屬香港特別行政區教育局。
資料來源:教育局(https://www.edb.gov.hk/)。
本工具僅作個人備份、查詢用途,不得作商業用途。
如發現資料與 EDB 官網不一致,以 EDB 官網為準。
開發者不對因使用本工具而產生嘅任何損失負責。
```

### 9.5 監管動態(可選監察)

- 香港《個人資料(私隱)條例》(PDPO)對學校影響大,但本工具唔收集個人資料,風險低
- AI 自動標註(二期)如涉及 LLM,需要留意《生成式 AI 沙盒》指引

---

## 10. 風險管理 (Risk Register)

| # | 風險 | 影響 | 機率 | 緩解策略 | 負責人 |
| --- | --- | --- | --- | --- | --- |
| R1 | ASP.NET WebForms scraper 太複雜,初期試唔到 | 高 | 中 | W1 立即 PoC;若失敗,fallback 用 Playwright(慢但穩) | 開發者 |
| R2 | EDB 改版,scraper 失效 | 高 | 中 | scraper 模塊化,加 unit test;每週 monitor;EDB 通常唔常改 | 開發者 |
| R3 | 學校拒絕採用(教育界對新工具接受度低) | 中 | 中 | 提供詳細 README + 一鍵 demo;邀請 KOL 教師試用 | 開發者 |
| R4 | PDF 解析失敗(掃描式 PDF) | 中 | 中 | pytesseract OCR 兜底;若失敗至少保留原 PDF | 開發者 |
| R5 | 跨年資料量過大,前端慢 | 中 | 低 | DuckDB 分區(按年);lazy load 詳情頁 | 開發者 |
| R6 | 開發者失去動力(個人項目,無 deadline) | 高 | 高 | 設定 M1/M2/M3/M4 硬 milestone;每 2 週自我 review | 開發者 |
| R7 | 版權爭議 | 高 | 低 | 嚴格遵守 § 9 法律章節嘅指引 | 開發者 |
| R8 | EDB 站 loading 慢,scraper timeout | 中 | 中 | timeout 30s;retry + backoff | 開發者 |
| R9 | 用戶 macOS / Windows 兼容性 | 中 | 中 | 兩平台都 test;launchd + Task Scheduler 都支援 | 開發者 |
| R10 | 通告主題分類字典不準 | 中 | 中 | MVP 階段只做基本分組;LLM 標註留二期 | 開發者 |

---

## 11. MVP 定義 (Minimum Viable Product)

### 11.1 MVP 範圍(2 週內完成)

**目標**: 證明「備份 + 本地搜尋」嘅核心價值。

**包含**:
- ✅ Python scraper:能夠備份過去 360 日嘅所有 EDB 通告(langno=2 繁中)
- ✅ DuckDB schema:儲存 metadata
- ✅ PDF 下載 + 儲存
- ✅ 簡單 Web UI:Vue 3 + Vite,顯示通告列表
- ✅ 基本搜尋:標題 keyword match
- ✅ README + start-demo.sh:一鍵啟動

**不包含**(留俾後續 sprint):
- ❌ 雙語(langno=3 簡中)
- ❌ 訂閱 / 通知
- ❌ 全文搜尋(只標題)
- ❌ 主題分類
- ❌ 匯出
- ❌ 排程自動化
- ❌ 過濾器

### 11.2 MVP 成功標準

| 指標 | 目標值 |
| --- | --- |
| 備份成功率 | ≥ 95%(允許少量 5xx / timeout) |
| 抓取一份通告所需時間 | ≤ 5 秒(含 PDF 下載) |
| 本地搜尋響應時間 | ≤ 500ms |
| 啟動 UI 時間 | ≤ 5 秒 |
| 備份 1 年通告嘅總時間 | ≤ 30 分鐘 |
| 程式碼測試覆蓋率 | ≥ 60% |

### 11.3 MVP 驗收測試(由開發者自評)

1. 跑 `python scraper.py --days 360` → 預期抓 ≥ 1,200 份通告(過去 360 日 EDB 平均量)。
2. 跑 `npm run dev`(Vue UI) → 喺 browser 見到列表。
3. 搜尋「公民教育」 → 預期至少 5 個結果。
4. 點擊其中一個 → 預期打開 PDF。
5. 離線狀態下重做 1-4 → 預期全部運作。

---

## 12. 開放問題 / 下一步

### 12.1 須 PM(開發者本人)確認嘅事項

1. **Q1: 工具嘅命名?** 暫定「EDB Circular Vault」/「教育通備」/「通勝」(教育界「通勝」= almanac,可能引起誤會)。需 PM 拍板。
2. **Q2: 發佈渠道?**
   - 選項 A: GitHub private repo + 一鍵本地 demo(跟 W1 偏好)
   - 選項 B: GitHub public repo(增加 star + 社區貢獻,但失去部分私隱)
   - 推薦: A
3. **Q3: 商業化?**
   - 選項 A: 純開源免費
   - 選項 B: 個人訂閱制(本地優先 SaaS,雲端只做 sync)
   - 推薦: A(先免費取用戶,二期再考慮 B)
4. **Q4: 開發優先級?**
   - 假設只有週末 / 工餘時間,W8 完成 MVP 合理?還是要做 W12?
   - 推薦: 預 W8,但容許 +2 週 buffer
5. **Q5: 用戶訪問時機?**
   - 訪問 5 位潛在用戶應喺 W1 末 / W2 初進行,先有方向感

### 12.2 立即可做嘅下一步(PM 建議)

1. **W0(本週)**: PM 確認 § 12.1 嘅 5 個問題。
2. **W1 開頭**:
   - 訪問 5 位潛在用戶(15-30 分鐘 each)
   - 跑 scraper PoC(用 Playwright / Python)
   - 決定開發環境(Mac / Windows / WSL)
3. **W1 末**:
   - 驗證 PoC 成功
   - 更新計劃書為 v0.2
   - 設定 W2 目標

### 12.3 關鍵假設(需驗證)

- A1: EDB 通告頁喺過去 5 年有 5,000-7,500 份通告
- A2: ASP.NET WebForms 結構穩定,scraper 可用 6 個月以上
- A3: DuckDB-WASM 喺用戶嘅 macOS 14+ / Windows 11 環境可運作
- A4: 用戶願意裝 Python + Node.js 環境,或用 Docker
- A5: 教師/行政人員願意用 desktop 工具,唔堅持 mobile-only

---

## 13. 附錄

### 13.1 EDB 通告站嘅 URL 結構

| 用途 | URL |
| --- | --- |
| 列表(繁中,過去 360 日) | `https://applications.edb.gov.hk/circular/circular.aspx?langno=2&circular_distribution=&search_type=1&issueDay=360` |
| 列表(簡中) | `https://applications.edb.gov.hk/circular/circular.aspx?langno=3&circular_distribution=&search_type=1&issueDay=360` |
| 列表(英文) | `https://applications.edb.gov.hk/circular/circular.aspx?langno=1&circular_distribution=&search_type=1&issueDay=360` |
| 詳情頁 | `https://applications.edb.gov.hk/circular/circular_memo.aspx?langno=2&circular_id=<id>` |

### 13.2 通告編號格式(sampling)

觀察所得,EDB 通告編號格式:`EDB(分組代號)編號/年份`,例如:
- `EDB(CM)175/2024` — Curriculum and Management
- `EDB(SCH ADM)67/2024` — School Administration
- `EDB(FE)12/2023` — Further Education

詳細分組代號需從 EDB 抓取時建立 lookup table。

### 13.3 參考資源

- 教育局通告主頁: https://www.edb.gov.hk/tc/about-edb/press/legco/index.html
- 政府版權聲明: https://www.gov.hk/tc/about/copyright/
- 個人資料私隱條例: https://www.pcpd.org.hk/tc_chi/data_privacy_law/ordinance_at_a_Glance/ordinance.html
- DuckDB-WASM 文件: https://duckdb.org/docs/api/wasm.html
- W1 項目參考(技術棧同私隱原則): `/Users/apple/.mavis/agents/main/memory/MEMORY.md`

### 13.4 文件版本控制

| 版本 | 日期 | 修改者 | 修改 |
| --- | --- | --- | --- |
| v0.1 | 2026-06-15 | Mavis(PM) | 初稿 |

---

## 14. PM 嘅一句話總結

呢個項目嘅核心價值唔係「技術有幾勁」,而係「**為教育界做一個佢哋用得著、本地、唔出街嘅工具**」。技術挑戰中等(ASP.NET scraper),法律風險低(政府公告可自由使用),市場窗口存在(教育界對本地工具有需求),但**最大嘅失敗風險係開發者(我自己)失去動力**——所以 MVP 要快、要見到成果、要有真實用戶試用反饋。

**先求有,再求好。W2 末如果 M1 達得到,項目就立得住。**

---

> **下一步**: 等待 PM(開發者本人)回應 § 12.1 嘅 5 個開放問題,然後即刻開始 W1 PoC。
