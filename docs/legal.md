# Legal — EDB Circular Vault

本文檔講解 EDB Circular Vault 的法律考慮。

## 角色聲明

本項目由**獨立開發者**個人維護,**與教育局無關**。本工具只係一個 open data 索引 / 永久 archive,並非教育局官方工具。

## 三層法律框架

### 第 1 層:EDB 原始 PDF

- **版權**:**© 教育局版權所有**(見 EDB 通告 footer)
- **使用條件**:香港政府公告一般容許使用及翻印,**須標明出處**
- **法律依據**:《版權條例》(香港法例第 528 章)第 198 條,政府公告的 fair dealing exception

### 第 2 層:Internet Archive mirror

- **版權**:EDB PDF 的版權（© 教育局）於 mirror 上**仍然存在**，但透過 IA 的 archive use case 處理
- **法律依據**:
  - IA 在美國 DMCA § 512 下有 safe harbor protection
  - 國際通行的 archive use case 原則(無商業目的、永久保存、研究用途)
  - EDB 站無 robots.txt,無明確禁止 archive
- **使用條件**:仍須標明出處為 EDB

### 第 3 層：本 repo 的 metadata（CC0 1.0）

- **版權**:**放棄所有版權**(CC0 1.0 Universal Public Domain Dedication)
- **可作任何用途**:商業、非商業、改作、再分發
- **不影響 EDB 本身的版權**：CC0 放棄的是 metadata（事實性資料，如日期、編號、標題），不影響 EDB 通告本身的 ©

## 為何 metadata 可用 CC0?

- **事實 vs 創作**:
  - 事實(日期、編號、學校類別)一般不受版權保護(Feist v. Rural, 美國最高法院 1991)
  - Metadata 集合係事實性 database,大部分司法管轄區(包括香港)對 database structure 有有限保護
- **Open data 慣例**:美國、英國、歐盟政府 open data 全用 CC0 或類似 waiver
- **鼓勵 reuse**:任何人都可商業 / 非商業用 metadata,例如學術研究、商業 dashboard、政策分析

## 為何 PDF 不 host 在 GitHub?

最初考慮過 host 在 GitHub 公開 repo，但有**多個 risks**：

| 風險 | 影響 | 機率 |
|---|---|---|
| **PDPO 違規** | EDB 通告可能含學生姓名(校內獎)、教師個人資料、家長通訊 | 高 |
| **EDB 版權投訴** | Mass redistribution 可能違反 EDB 站 ToS,觸發 takedown | 中 |
| **永久私隱** | 一旦公開,搜尋引擎永久 index,無法撤回 | 高 |
| **同 W1 偏好矛盾** | 用戶之前 W1 明確要求 private repo | N/A |

**Solution**:PDF 透過 Internet Archive mirror(archive use case safe harbor),GitHub 只 host metadata。

## PDPO 私隱考慮

- **GitHub 不 host 任何 PDF** → PDPO 私隱風險**完全歸零**
- **Internet Archive 係公開 mirror** → 任何人都可 access,但 IA 已有 archive use case 保護
- **EDB 通告可能含 PDPO 敏感資料** → 這是 EDB 站本身的問題，不是我們 archive 的問題
- **本工具的責任**：
  - 透明(README 講明)
  - attribution 完整
  - 不修改原文
  - 不 collect 任何 user data

## 免責聲明(本 repo 採用)

```
本工具(EDB Circular Vault)為非官方 open data 索引工具。

Metadata 部分:
- 以 CC0 1.0 Universal 釋出,放棄我們部分版權
- 鼓勵任何 reuse(商業 / 非商業)
- 須保留 attribution 標明出處為教育局

PDF 部分:
- 由 Internet Archive 永久 mirror
- 原始版權屬香港特別行政區教育局(© 教育局版權所有)
- 僅作 archive / 研究用途,非官方 source of truth
- 如發現資料與 EDB 官網不一致,以 EDB 官網為準

工具使用須知:
- 本工具非官方,與教育局無關
- 開發者不對因使用本工具而產生的任何損失負責
- Internet Archive link 雖永久但非保證,建議用戶自備本地備份
```

## 用戶責任

使用本工具的用戶應：

1. **尊重 EDB 的 ©**：即使 metadata 是 CC0，PDF 的版權仍屬 EDB
2. **標明出處**:re-use metadata 時保留 attribution
3. **不做惡意用途**：例如 scraper 商業轉售、聲稱是官方、modified PDF
4. **如有法律疑慮**:諮詢專業律師

## 開發者聲明

- 開發者係獨立個人,**並非律師**
- 本文檔**不是法律意見**（legal advice）
- 如有重大法律疑慮,請諮詢合資格的香港事務律師
- 開發者對錯誤使用本工具而產生的任何後果不負責

## 變更記錄

| 日期 | 修改 |
|---|---|
| 2026-06-16 | 初稿,對應 project plan v0.2 §9 |
