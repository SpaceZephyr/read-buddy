---
name: read-weread-export
description: 导出微信读书划线笔记为 Markdown 或 PDF 文件。当用户说"导出我的微信读书划线"、"导出读书笔记"、"把划线保存下来"、"weread 导出"时触发。依赖 weread-skills 调用接口，按书籍-章节分组排版，附划线时间，输出美观的笔记文档。
---

# weread-export — 微信读书划线笔记导出

## 触发条件

用户说：
- 导出我的所有微信读书划线笔记
- 导出读书笔记
- 把我的划线保存成文件
- 备份微信读书笔记
- export weread notes

## 前置依赖

- 已安装 `weread-skills`（同目录下）
- 环境变量 `WEREAD_API_KEY` 已配置

## 工作流

### 步骤 1：询问格式、范围、保存位置（每次必问，不可省略）

**无论触发语中是否提到这些信息，每次执行都必须先把三个问题问完再动手。** 即使用户说"导出全部为 PDF"，也要复述确认一遍。

一次问完三个问题：

```
请确认导出参数：

1. 输出格式？
   a. Markdown（.md）
   b. PDF（.pdf）
   c. 两个都要

2. 导出范围？
   a. 全部书籍
   b. 指定书籍（请告诉我书名或 bookId）

3. 保存到哪个目录？
   - 直接回车 = 当前工作目录
   - 或者输入一个绝对路径 / 相对路径（如 ~/Documents/微信读书）
```

收到用户答复后再进入步骤 2。如果答复不清晰（例如只回了格式没回范围），追问缺失的那一项，不要默认。

保存路径处理：
- 用户给的是绝对路径：原样使用
- 用户给的是相对路径：相对当前工作目录展开
- 用户直接回车：使用当前工作目录
- 路径不存在：自动 `mkdir -p` 创建，不再追问

### 步骤 2：拉取笔记本概览

调 `/user/notebooks` 分页拉取所有有笔记的书：

```json
{"api_name":"/user/notebooks","count":50,"skill_version":"1.0.3"}
```

`hasMore=1` 时，用最后一项的 `sort` 作为 `lastSort` 继续拉。**参数必须平铺在 body 顶层，不要包在 `params` 里**。

汇总：
- `totalBookCount`：书籍数
- 累加各书 `noteCount + reviewCount` 作为总笔记数

### 步骤 2.5：指定书籍不在书架上的处理

如果用户在步骤 1 选了"指定书籍"，但该书 **不在 `/user/notebooks` 的返回结果中**（说明用户没有个人划线/笔记），必须先问用户：

```
你的书架上没有《xxx》的个人笔记。
要改为导出这本书的【热门划线】（其他读者的高频划线）吗？

a. 是，导出热门划线
b. 否，取消导出
```

如果用户选 a：
- 调 `/store/search` 拿到 bookId（如果用户给的是书名）
- 调 `/book/chapterinfo` 拿章节列表
- 调 `/book/bestbookmarks`（bookId, chapterUid=0）拿全书 Top 20 热门划线
- 在 Markdown 顶部标注 **"热门划线导出（非个人笔记）"**，每条划线下方显示划线人数（`totalCount` 字段，格式 `🔥 N 人划线`），不显示时间

### 步骤 3：逐本拉划线和想法

对每本书并行调两个接口：

```json
{"api_name":"/book/bookmarklist","bookId":"<bookId>","skill_version":"1.0.3"}
{"api_name":"/review/list/mine","bookid":"<bookId>","count":100,"skill_version":"1.0.3"}
```

注意：`/review/list/mine` 的字段名是 `bookid`（全小写），不是 `bookId`。

### 步骤 4：组装 Markdown

按下方模板生成。文件保存到步骤 1 用户指定的目录，文件名固定为 `微信读书划线-YYYY-MM-DD.md`。

#### Markdown 模板

```markdown
# 微信读书划线笔记

> **导出时间**：YYYY-MM-DD HH:MM
> **共 N 本书 · X 条划线 · Y 条想法**

---

## 目录

1. [书名 A](#1-书名-a) · 12 划线
2. [书名 B](#2-书名-b) · 5 划线 / 2 想法

---

## 1. 书名 A

**作者**：xxx
**最近笔记**：YYYY-MM-DD
**统计**：12 划线 / 0 想法 / 进度 45%

### 第三章 章节名

> 划线原文……

📅 2025-09-21

> 第二条划线……

📅 2025-09-22
💭 我对这条的想法（如果有 review 关联到这条划线）

---

## 2. 书名 B

……
```

排版要点：
- 书名用 `##`，章节用 `###`
- 划线正文用 `>` 引用块
- 时间格式 `YYYY-MM-DD`（不带时分秒）
- 想法在划线下方用 `💭` 前缀
- 整本书评（reviews 中 `chapterName` 为空）单独放在该书末尾"## 整本书评"小节
- 每本书之间用 `---` 分隔
- 顶部"共 N 本书 · X 条划线 · Y 条想法"用粗体

**排序规则（强制）：**
1. **章节顺序**：严格按 `chapters[].chapterIdx` 升序排列；从 `/book/bookmarklist` 或 `/book/bestbookmarks` 回包的 `chapters` 数组拿到章节顺序，**不要按笔记创建时间排**
2. **章节内划线顺序**：按 `range` 起始位置（`range` 字段 `-` 前的数字，转为 int）升序，保证划线在文中出现的先后顺序
3. **跨章节的想法/书评**：`chapterName` 为空的整本书评单独放在该书末尾
4. **未匹配章节**：从 `chapters` 中找不到对应 `chapterUid` 的划线归到该书末尾"### 未分类"小节
5. 排序在生成 Markdown 前完成，禁止在输出阶段乱序

### 步骤 5：如需 PDF，转换

如果用户要 PDF，对生成的 MD 执行：

```bash
python3 ~/.claude/skills/read-weread-export/scripts/md_to_pdf.py <md路径> <pdf路径>
```

脚本依赖 Chrome（macOS 自带或已安装）。失败时回退到 Markdown 并提示用户。

### 步骤 6：报告结果

输出：
- 文件路径（可点击打开）
- 统计：N 本书 / X 划线 / Y 想法
- 如果导出耗时较长，提示进度

## 注意事项

1. **不要重复请求**：如果在同一轮对话已经调过 `/user/notebooks`，直接复用结果
2. **大量笔记**：超过 30 本书时分批并行调用接口（每批 5 本），避免请求堆积
3. **空数据**：某本书 `bookmarklist` 为空（只有书签没有划线）时，在导出中标注"（仅书签，无可导出划线）"
4. **时间戳转换**：所有 `createTime` 转为 YYYY-MM-DD 格式（用户时区按本机）
5. **想法与划线关联**：`/review/list/mine` 返回的 review 如果包含 `range` 字段且匹配某条划线的 range，则贴在该划线下方；否则放章节末尾或全书末尾
6. **章节标题**：从 `bookmarklist` 回包的 `chapters` 数组按 `chapterUid` 映射；未匹配章节归到"## 未分类"
7. **文件名安全**：书名中的 `/`、`:` 等字符替换为 `-`
