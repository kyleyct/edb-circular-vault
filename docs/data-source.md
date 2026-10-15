# Data Source — EDB Circular 通告站

本文檔描述本項目如何 scrape 教育局通告站，以及相關的 methodology。

## 來源 URL

**主站**:`https://www.edb.gov.hk/tc/about-edb/forms-and-circulars/index.html`
**應用站**:`https://applications.edb.gov.hk/circular/circular.aspx?langno={langno}`

`langno` 對應:
- `1` = English
- `2` = 繁體中文(default)
- `3` = 簡體中文

## 通告編號格式

EDB 通告編號格式:`EDB[C|CM]NNN/YYYY`

- `EDBC` = EDB Circular(通告)
- `EDBCM` = EDB Circular Memorandum(通函)
- `NNN` = 流水號(000-999)
- `YYYY` = 年份

例:`EDBCM082/2026` = 2026 年第 82 份通函。

## 通告保留期

**EDB 站只保留過去 360 日（1 年）的通告**。過期即清除，無 archive 機制。

這是本項目的核心動機：建立永久 archive。

## 數據源結構

EDB 通告搜尋結果頁(`circular.aspx` 用 POST 表單 query 後)直接列 PDF 連結,**不需要 detail 頁**。

每個 circular entry 係一個 `<tr>`,包含 3 個 `<td>`:

| Column | 內容 |
|---|---|
| td1 | 發出日期 (`dd/mm/yyyy` 歐式) |
| td2 | 主題(標題) + 通告編號 + 摘要 + 學校類別 |
| td3 | 語言(英文 / 繁中 / 簡中 PDF 連結) |

PDF URL 格式:`https://applications.edb.gov.hk/circular/upload/EDBC(M)/XXXX[C|E|S].pdf`

- `C` suffix = 繁體中文 (`zh-HK`)
- `E` suffix = 英文 (`en`)
- `S` suffix = 簡體中文 (`zh-CN`)

部分通告**只有部分語言**（常見情況：有繁中，不一定有英文）。

## Scraping methodology

### POST 表單(ASP.NET WebForms)

EDB 站是傳統 ASP.NET WebForms，搜尋表單是 POST 而不是 GET。

每次 POST 都要帶:
- `__VIEWSTATE`(base64-encoded server state,~2.7KB)
- `__EVENTVALIDATION`(server-side validation token,~1.1KB)
- `__VIEWSTATEGENERATOR`(server-side state version)
- 表單 fields(`txtKeyword`, `ddlSchoolType2`, `ddlCircularType`, `txtCircularNumber`, `txtPeriodFrom`, `txtPeriodTo`)
- Submit button field(`btnSearch2` = "搜尋")

### 流程

1. GET `circular.aspx?langno=2` → 拎 `__VIEWSTATE` 等 hidden fields
2. POST `circular.aspx?langno=2` 表單(設定 period + filter)→ 拎 search result HTML
3. Parse HTML `<tr class="circularResultRow">` 拎 metadata
4. 對每份通告 GET 對應 PDF URL → 下載 + SHA-256 hash

### Rate limiting

**預設 1.5s/req**(避免對 EDB 站造成負擔)。

### Retry policy

- 預設 3 retries, exponential backoff(2/4/8 sec)
- HTTP 5xx / timeout / connection error 都 retry
- HTTP 4xx (except 429) 不 retry（代表 client error）

## Scraping 限制

- **360 日 retention**:EDB 站過期清除,本工具 scrape 最多 360 日
- **Archive.org safe harbor**:PDF 永久 mirror 在 archive.org，解決 EDB 清除問題
- **三語不齊**：部分通告只有部分語言版本，scrape 不齊是正常
- **公告 / 表單 / 表格**:本項目只 scrape 通告（circular + memorandum），不包括其他類型文件

## 私隱考慮

本項目只 scrape 公開資料:

- EDB 通告是政府公開資訊，本來就在 internet 上 free access
- 我們不收集任何 user data、不 set tracking cookies
- 抓取的 PDF 透過 Internet Archive 永久 mirror（archive use case safe harbor）
- GitHub repo **不 host 任何 PDF**，只 metadata，完全避免 PDPO 風險

## 法律考慮

- 香港政府公告一般容許使用及翻印,須標明出處
- 我們在 metadata 內 explicit 標明「資料來源：教育局(https://www.edb.gov.hk/)」
- Internet Archive 對 archive use case 有 safe harbor(per DMCA § 512 的類比)
- 開發者不是律師，如有法律疑慮請諮詢專業意見

## Reproducing scrape

要 reproduce 完整 scrape:

```bash
# 預設:增量 7 日, 繁中
python3 tools/scraper.py

# 完整 360 日, 繁中
python3 tools/scraper.py --days 360 --lang zh-HK

# 完整 360 日, 三語
python3 tools/scraper.py --days 360 --lang all

# 自定 period
python3 tools/scraper.py --from 2024-01-01 --to 2024-12-31

# Dry run（只 parse，不下載 PDF）
python3 tools/scraper.py --dry-run
```

預期 runtime:**6-8 分鐘**(187 份 × 1.5s/req + PDF download)
