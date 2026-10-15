# Schema — EDB Circular Metadata

本文檔詳述 `data/metadata.json` 及 `data/circulars.csv` 的 schema。

## 主 schema (`data/schema/metadata.schema.json`)

JSON Schema draft-07 格式,符合 [json-schema.org](https://json-schema.org/) 標準。

### Top-level 欄位

| Field | Type | Required | 說明 |
|---|---|---|---|
| `schema_version` | string | ✓ | Schema 版本(語義化版本),e.g. `"1.0"` |
| `generated_at` | string (date-time) | ✓ | metadata 產生時間(ISO 8601 + timezone) |
| `tool` | string | ✓ | 產生此 file 的工具名，e.g. `"EDB Circular Vault"` |
| `tool_version` | string | ✓ | 工具版本(semver) |
| `source` | string | ✓ | 資料來源名稱 |
| `source_url` | string (uri) | ✓ | 資料來源 URL |
| `license` | string | ✓ | License 標示(本項目: `CC0 1.0`) |
| `attribution` | string | ✓ | 歸屬標示 |
| `disclaimer` | string | ✓ | 免責聲明 |
| `circulars` | array | ✓ | Circular 列表,每個 element 對應 `#/definitions/circular` |

### Circular object 欄位

| Field | Type | Required | 說明 |
|---|---|---|---|
| `circular_id` | string | ✓ | EDB 內部 ID,從 PDF URL 推導,e.g. `EDBCM26082` |
| `circular_no` | string | ✓ | 對外通告編號,e.g. `EDBCM082/2026` |
| `title` | string | ✓ | 通告標題(1-500 chars) |
| `issue_date` | string (date) | ✓ | 發出日期(YYYY-MM-DD) |
| `lang` | enum | ✓ | 語言:`zh-HK` / `zh-CN` / `en` |
| `distribution` | array of string | | 分發組別,e.g. `["中學", "小學", "幼稚園"]` |
| `subject` | string \| null | | 主題(一期 `null`,二期 LLM 標註) |
| `summary` | string | | 摘要(最多 5000 chars) |
| `source_url` | string (uri) | ✓ | EDB 站原始 PDF URL |
| `archive_url` | string \| null | ✓ | Internet Archive 永久 mirror URL(一期可 `null`,T3 完成後填寫) |
| `archive_metadata_url` | string \| null | | Internet Archive item metadata page URL(可選) |
| `pdf_size_bytes` | integer | | PDF file size(bytes) |
| `pdf_pages` | integer | | PDF 頁數 |
| `pdf_sha256` | string (64-hex) | ✓ | PDF SHA-256 hash(lowercase hex) |
| `scraped_at` | string (date-time) | | Scrape 時間 |
| `scraper_version` | string | | Scraper 版本 |

### Schema 演進

Schema 版本用 [Semantic Versioning](https://semver.org/):

- **Major**:Breaking change(加 required field,改 field type)
- **Minor**:Backward-compatible new field
- **Patch**:Documentation / typo fix

加 required field 算 breaking change,需要 bump major version + migration plan。

## CSV 格式 (`data/circulars.csv`)

CSV 對應 `circulars` array,每個 row 一份通告,columns 同 `circular` object fields。

**特別處理**:
- `distribution` 係 array → CSV 用 `|` delimiter(避免 CSV quote escape 問題),e.g. `中學|小學|幼稚園`
- `null` 值 → empty string
- `archive_url` 一期為 empty string(待 T3 完成後填寫)
- `scraped_at` → 直接用 ISO 8601 string

## 驗證

用 `tools/validate.py` 驗證 `data/metadata.json`:

```bash
python3 tools/validate.py data/schema/metadata.schema.json data/metadata.json
```

輸出:
- `OK: <file> validates against <schema>` — 通過
- `FAIL (N error(s)):` — 失敗,列出每個 error path

## 範例

```json
{
  "schema_version": "1.0",
  "generated_at": "2026-06-16T22:45:49+08:00",
  "tool": "EDB Circular Vault",
  "tool_version": "0.2.0",
  "source": "Education Bureau, HKSAR Government",
  "source_url": "https://www.edb.gov.hk/tc/about-edb/forms-and-circulars/index.html",
  "license": "CC0 1.0 Universal (Public Domain Dedication) - metadata only",
  "attribution": "資料來源:教育局(https://www.edb.gov.hk/)。本工具僅提供 metadata 索引,PDF 透過 Internet Archive 永久 mirror。",
  "disclaimer": "本工具非官方 open data 索引工具,與教育局無關。",
  "circulars": [
    {
      "circular_id": "EDBCM26082",
      "circular_no": "EDBCM082/2026",
      "title": "由課程及質素保證科分發的學與教材料",
      "issue_date": "2026-06-15",
      "lang": "zh-HK",
      "distribution": ["中學", "小學", "資助中學", "資助小學"],
      "subject": null,
      "summary": "本通函旨在通知各幼稚園、小學及中學校長...",
      "source_url": "https://applications.edb.gov.hk/circular/upload/EDBCM/EDBCM26082C.pdf",
      "archive_url": null,
      "archive_metadata_url": null,
      "pdf_size_bytes": 1175164,
      "pdf_pages": 13,
      "pdf_sha256": "1bd92cbd41d73c6f70e0c852dde5348a632eb9b252b8895ee0f1dcded06db897",
      "scraped_at": "2026-06-16T22:39:55+08:00",
      "scraper_version": "0.2.0"
    }
  ]
}
```
