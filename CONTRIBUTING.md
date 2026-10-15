# Contributing to EDB Circular Vault

歡迎參與貢獻！本項目旨在為香港教育界建立永久可訪問的 EDB 通告 metadata 索引。

## 點樣 contribute?

### 1. 報錯 metadata(最常見)

如果你發現某份通告的 metadata 不正確（標題錯、日期錯、分發組別錯等）：

1. 開 [Issue](../../issues/new/choose)
2. 選 "Data correction" template
3. 填寫以下資料:
   - `circular_id`(e.g. `EDBCM26082`)
   - 邊個 field 錯
   - 應該係乜嘢
   - 來源(可以係 EDB 站 link)

或者直接 PR 修改 `data/metadata.json`，然後在 PR 描述中 cite 來源。

### 2. 翻譯 docs

歡迎翻譯 `docs/` 內的中文文檔為英文或其他語言。

```bash
docs/
├── data-source.md       # 翻譯去英文
├── schema.md
├── legal.md
├── internet-archive-policy.md
└── faq.md
```

### 3. 改良 source code

歡迎 PR 到:
- `tools/scraper.py` — 加 features(LLM 主題標註、新 language support 等)
- `tools/ia_uploader.py` — 加 features(better retry, batch upload, 等)
- `tools/validate.py` — 加 JSON Schema keywords 支援

**Coding 風格**:
- stdlib preferred(已係 90% stdlib)
- 香港繁體書面語 for user-facing strings
- PEP 8 compliant
- Public function + class 加 docstring

### 4. 改善 documentation

- 修正錯別字、grammar
- 加 FAQ entry
- 改善 schema doc

### 5. 贊助 IA upload

如果你有 IA account，可以幫忙 upload 缺失的 PDF 到 Internet Archive。請先在 Issue 說明，免得重複 upload。

## Development Setup

```bash
# Clone repo
git clone https://github.com/USER/edb-circular-vault.git
cd edb-circular-vault

# (可選) Setup venv
python3 -m venv .venv
source .venv/bin/activate

# Install optional deps(只 IA uploader + scraper 需要)
pip install internetarchive beautifulsoup4 lxml

# Test scraper
python3 tools/scraper.py --dry-run --days 7
```

## 行為守則

- 不要 fabricate / mock 任何 metadata（本項目 hard rule）
- 不要在 GitHub repo host 任何 PDF（方案 A 的 privacy + legal 防線）
- 尊重 EDB 站 rate limit(預設 1.5s/req)
- 用香港繁體書面語 for user-facing content(per user preference)

## Pull Request Process

1. Fork repo
2. Create feature branch (`git checkout -b feature/your-feature`)
3. Commit changes
4. Push branch
5. 開 PR,描述:
   - 改了甚麼
   - 為何
   - 有否 breaking change
6. 等待 review

## 版本控制

- 主版本:breaking change
- 次版本:new feature
- 修訂版本:bug fix

參考 [Semantic Versioning](https://semver.org/)。

## License

Contributions 將以 [CC0 1.0](LICENSE-CC0)(data) / [MIT](LICENSE-MIT)(code) 釋出,同 project 一致。
