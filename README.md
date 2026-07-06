<h1 align="center">Read Buddy</h1>

<p align="center"><code>read-buddy.skill</code></p>

<p align="center"><em>「你想读懂的下一份信息，何必先被格式困住」</em></p>

<p align="center">
  <img alt="License MIT" src="https://img.shields.io/badge/License-MIT-c8a500?style=for-the-badge">
  <img alt="Agent Skills Standard" src="https://img.shields.io/badge/Agent%20Skills-Standard-5aa524?style=for-the-badge">
  <img alt="skills.sh Compatible" src="https://img.shields.io/badge/skills.sh-Compatible-1888c8?style=for-the-badge">
  <img alt="Runtime" src="https://img.shields.io/badge/Runtime-Claude%20Code%20%C2%B7%20Codex%20%C2%B7%20Cursor%20%C2%B7%20OpenClaw%20%C2%B7%20Hermes-7b2bd9?style=for-the-badge">
</p>

<p align="center">
  公众号 / 小红书 / B站 / 知乎：<strong>空格的键盘</strong> ｜ <a href="mailto:wzfh520@gmail.com">wzfh520@gmail.com</a>
</p>

Read Buddy 是一套给内容创作者、研究者、产品人和知识工作者用的信息读取 Skill 集合。

它帮你把网页、RSS、YouTube、播客、X/Twitter、飞书文档、图片 OCR、微信读书、个人阅读记录和热点信号，转成可读、可检索、可总结、可继续写作的结构化内容。

基于开放的 Agent Skills 协议，可在 Claude Code、Codex、Cursor、OpenClaw、Hermes Agent、CodeBuddy、Workbuddy、Gemini CLI、OpenCode 等兼容 runtime 中运行。

不是让 AI 凭空总结一段它没读过的材料。

是先把来源内容拿回来，再让 Agent 帮你完成：

- 读网页、转 Markdown、保留元数据
- 读 YouTube 字幕、播客更新和长内容
- 读 RSS 和 AI 热点，形成每日信息面
- 读飞书文档、图片/PDF OCR、个人历史数据
- 读微信读书划线、书架和阅读数据，生成导出、分析和回顾
- 读 X/Twitter 内容和博主风格，但明确反爬与同意边界
- 把长内容消化成摘要、选题、长文或短帖

看效果 · 安装 · 它能读什么 · 使用方式 · 工作原理 · 诚实边界

## 效果示例

```text
用户      ❯ 把这篇网页转成 Markdown

助手      ❯ 已读取 URL，完成正文提取。

            输出包含：
            - 标题、作者、发布时间
            - 正文 Markdown
            - 原文链接
            - 图片引用

            已过滤导航、广告、页脚等噪声。
```

再看 YouTube：

```text
用户      ❯ 帮我提取这个 YouTube 视频字幕并总结

助手      ❯ 已提取字幕，优先语言：中文 / 英文。

            主要观点：
            1. AI Agent 的价值不在替代按钮，而在连接上下文
            2. 工作流稳定性比单次模型能力更重要
            3. 好的工具应该留下可复用的中间产物

            可继续生成：短帖、长文、金句、选题卡。
```

再看热点采集：

```text
用户      ❯ 看看最近 3 天 AI 圈有什么新东西

助手      ❯ 已聚合 RSS / Product Hunt / Hacker News / 官方博客 / X 公开信息。

            今日值得关注：
            - 新模型发布：适合写快讯
            - AI 编程产品更新：适合做教程
            - Agent 工作流案例：适合拆方法论
            - 开源项目上榜：适合做选题池
```

Read Buddy 的目标不是囤信息。  
它负责把信息变成下一步可以用的材料。

## 安装

Read Buddy 基于开放的 Agent Skills 协议，可在任何 skills-compatible 的 AI agent runtime 中运行。

### 方式一：一行命令（推荐，跨 runtime）

打开你正在用的 agent（Claude Code、Codex、Cursor、OpenClaw、Hermes、CodeBuddy、Workbuddy、Gemini CLI、OpenCode 等），告诉它：

```text
帮我安装这个 skill：https://github.com/SpaceZephyr/read-buddy
```

或者用通用 CLI 安装器（vercel-labs/skills，支持多 runtime）：

```bash
npx skills add SpaceZephyr/read-buddy
```

它会自动识别你当前的 runtime 并把 skill 放到正确目录。需要指定时可加 runtime 参数，例如 `-a codex` / `-a claude-code` / `-a cursor`。

### 方式二：手动安装

克隆仓库后，把需要的 skill 目录复制到你的 runtime skills 目录：

```bash
git clone https://github.com/SpaceZephyr/read-buddy.git
```

仓库结构：

```text
read-content-digest/
read-feishu-doc/
read-ocr/
read-personal-data-harvester/
read-podcast-script-generator/
read-podcast-workflow/
read-rss-aggregator/
read-topic-collector/
read-url-markdown/
read-weread-analyzer/
read-weread-coach/
read-weread-export/
read-web-article-translator/
read-web-scraper/
read-x-blogger-analyzer/
read-x-markdown/
read-xiaoyuzhou-article/
read-youtube-feed/
read-youtube-transcript/
```

每个子目录都是一个独立 Skill。

### 命名规范

Read Buddy 内所有 Skill 都统一使用 `read-*` 命名，目录名与 `SKILL.md` 里的 `name` 保持一致。

- `read-`：表示这是 SpaceZephyr 体系下的信息读取与消化类 Skill。
- 中间词：说明来源或对象，例如 `youtube`、`x`、`rss`、`web`、`feishu`。
- 后缀词：说明动作或输出，例如 `markdown`、`transcript`、`digest`、`aggregator`、`translator`。

例如：`read-url-markdown` 把网页转成 Markdown，`read-youtube-transcript` 提取 YouTube 字幕，`read-content-digest` 消化长内容。

### 方式三：作为参考资料使用

即使你的 runtime 不支持 Agent Skills 自动加载，也可以直接打开对应目录里的 `SKILL.md`，把内容粘贴进对话。  
它本质是一份 markdown + YAML frontmatter + 可运行脚本或工作流说明。

## 使用

装好后，可以直接告诉 agent：

```text
把这个网页保存成 Markdown
```

```text
提取这个 YouTube 视频的中文字幕
```

```text
把这个小宇宙单集转成文章
```

```text
把这篇播客摘要改成口播脚本
```

```text
最近 3 天 RSS 有什么更新
```

```text
分析这个 X 博主的内容风格
```

```text
把这篇英文网页翻译成中文 Markdown
```

```text
读取这个飞书文档
```

```text
导出我的微信读书划线
```

```text
分析我的微信读书，生成阅读画像
```

```text
把这张图里的文字 OCR 出来
```

```text
开始今日 AI 热点采集
```

## 它能读什么

| Skill | 解决的问题 | 输出 |
| --- | --- | --- |
| `read-url-markdown` | 用 Chrome CDP 读取网页，支持登录态页面等待后转 Markdown | Markdown |
| `read-web-scraper` | 轻量网页抓取，把 HTML 正文转 Markdown | Markdown / raw HTML |
| `read-web-article-translator` | 在线文章翻译为中文并保存 Markdown | 中文 Markdown |
| `read-x-markdown` | X/Twitter 推文、线程、文章转 Markdown，使用前需明确同意风险 | Markdown + YAML |
| `read-x-blogger-analyzer` | 分析 X/Twitter 博主内容风格、爆款原因和增长策略 | 分析报告 |
| `read-youtube-feed` | 获取关注 YouTube 博主/播客的近期更新 | 更新列表 |
| `read-youtube-transcript` | 提取 YouTube 字幕并转成中文文字稿 | Markdown / text / JSON |
| `read-podcast-workflow` | YouTube 播客更新选择、字幕提取、内容消化、飞书保存 | 工作流产物 |
| `read-podcast-script-generator` | 播客笔记、摘要、文稿改写成视频口播脚本 | 口播脚本 |
| `read-xiaoyuzhou-article` | 小宇宙单集音频下载、Groq Whisper 转录、整理成文章 | 文稿 + 文章 |
| `read-rss-aggregator` | 聚合 OPML 中的 RSS 源近期更新 | 更新摘要列表 |
| `read-topic-collector` | 采集 AI 热点、产品发布、论文、博客和社区动态 | 结构化热点清单 |
| `read-content-digest` | 长文、播客、访谈、文章转短帖和长文叙事 | 摘要 / 短帖 / 长文 |
| `read-feishu-doc` | 通过飞书开放 API 读取飞书文档和 blocks | 文档内容 / blocks JSON |
| `read-ocr` | 图片、PDF、扫描件 OCR 识别 | 结构化 JSON / 文本 |
| `read-weread-export` | 导出微信读书个人划线和想法，支持 Markdown / PDF | 读书笔记文件 |
| `read-weread-analyzer` | 基于书架、阅读时长、划线和想法生成 10 维度阅读分析 | 9:16 HTML 阅读报告 |
| `read-weread-coach` | 用已读书做阶梯书单、写作引用和每日划线回顾 | 推荐 / 引用 / 回顾 |
| `read-personal-data-harvester` | 采集用户自己的阅读、观看、收藏历史到本地数据库 | SQLite / 结构化数据 |

## 使用方式

你可以用自然语言直接触发，也可以点名调用单个 Skill。

| 方式 | 示例 | 会触发什么 |
| --- | --- | --- |
| URL 读取 | `把这个网页转 Markdown`、`保存这篇文章` | 读取网页正文、清理噪声、输出 Markdown |
| 视频/播客 | `提取这个 YouTube 字幕`、`处理这个播客` | 拉字幕、生成文字稿、可继续摘要和入库 |
| 小宇宙播客 | `小宇宙转文字`、`把这个小宇宙链接转成文章` | 下载音频、切片转录、生成文稿和文章 |
| 口播脚本 | `改成口播`、`生成播客脚本` | 把播客摘要改写成第一人称视频脚本 |
| 信息流更新 | `最近 RSS 有什么`、`获取播客更新` | 聚合 RSS 或 YouTube 关注源 |
| 热点采集 | `开始今日选题`、`今日 AI 热点` | 多源搜索并生成结构化热点列表 |
| 内容消化 | `总结这篇长文`、`生成短帖和长文版` | 提炼观点、反共识、金句和叙事结构 |
| 文档读取 | `读取这个飞书文档`、`提取 blocks` | 调用飞书 API 获取文档内容 |
| OCR 读取 | `识别这张图`、`提取 PDF 文字` | 调用 OCR 脚本返回文本和置信度 |
| 微信读书 | `导出我的微信读书划线`、`分析我的微信读书`、`今日笔记` | 导出笔记、生成阅读报告、抽取历史划线 |
| X 分析 | `保存这条推文`、`分析这个博主` | 转 Markdown 或生成博主分析报告 |
| 个人数据 | `同步我的读书记录`、`采集我的收藏` | 在本机建立个人内容历史采集管道 |

## 工作原理

Read Buddy 不是一个单一爬虫，而是一组信息读取和消化 Skill。

它把阅读任务拆成四层：

| 层次 | 说明 |
| --- | --- |
| 来源接入 | URL、RSS、YouTube、X、飞书、OCR、微信读书、本地文件、个人平台数据 |
| 内容抽取 | HTML 清洗、字幕提取、OCR、API blocks、线程解析、RSS 条目聚合 |
| 结构化整理 | Markdown、JSON、SQLite、YAML front matter、更新列表、分析报告 |
| 认知处理 | 摘要、翻译、热点判断、风格分析、选题提炼、长短文改写 |

常见分支：

- 网页读取：优先用轻量抓取，遇到登录态或 JS 渲染页面时使用 Chrome CDP。
- 视频播客：先获取更新或字幕，再交给 `read-content-digest` 做观点提炼；小宇宙单集可走 `read-xiaoyuzhou-article` 下载音频并转写。
- 口播创作：播客摘要或结构化笔记可交给 `read-podcast-script-generator` 改成视频口播稿。
- 热点采集：先收集多源链接，再按来源、主题和选题价值整理。
- X 内容：能手动就手动，自动抓取需要用户知情并接受反爬风险。
- 微信读书：依赖官方 `weread-skills` 提供的 API Gateway 和用户自己的 `WEREAD_API_KEY`。
- 个人数据：只处理用户自己的数据，默认本地保存，不上传。

## 适合谁

- 自媒体作者：读网页、读视频、读热点，沉淀选题和素材
- 研究者：聚合 RSS、论文、官方博客和访谈内容
- 产品经理：追踪竞品动态、用户讨论、行业新闻
- 播客听众：把 YouTube / 小宇宙播客转文字稿、摘要、文章和口播脚本
- 知识管理用户：把网页、飞书、个人历史数据转成本地知识库
- 内容运营：分析 X 博主、热点来源和内容风格

## 风控与安全性说明

Read Buddy 的定位是公开内容读取、个人数据整理和知识消化，不是账号自动化或大规模爬虫工具。

- 只读优先：默认只读取公开内容、用户提供的链接、用户本机文件或用户自己的平台数据。
- 不做账号动作：不执行发帖、点赞、评论、关注、私信、批量互动等写操作。
- 凭据不入库：飞书 app secret、Cookie、API Key、`.env`、浏览器登录态和个人数据库都不应提交到仓库。
- 微信读书数据：只处理用户授权后的个人书架、划线、想法和阅读数据，报告发布前应脱敏。
- X 风险提示：`read-x-markdown` 使用非官方接口，必须先获得用户同意，并告知可能失效或触发平台限制。
- 个人数据本地化：`read-personal-data-harvester` 默认只在用户设备上采集和保存，不上传到第三方。
- 小宇宙转写：`read-xiaoyuzhou-article` 需要 `ffmpeg` 和 `GROQ_API_KEY`，音频下载与转录应仅用于你有权处理的内容。
- 低频采样：RSS、网页、YouTube、X 等来源应低频、按需读取，避免给平台造成压力。
- 分享前脱敏：报告和 Markdown 发布前移除 Cookie、token、邮箱、手机号、私密链接和未公开账号信息。

## 诚实边界

每个信息读取工具都应该说明自己做不到什么。

- 不是实时全网监控：RSS、搜索、YouTube 和网页结果都受来源更新和接口限制影响。
- 抓取不保证成功：登录、验证码、Cloudflare、JS 渲染、反爬和地区限制都可能失败。
- OCR 会出错：低清图片、复杂表格、手写体和多语言混排需要人工复核。
- 自动摘要和口播脚本不等于原文：`read-content-digest` / `read-podcast-script-generator` 会压缩、重组和改写观点，关键事实仍应回看原始文稿。
- X 自动抓取成功率低：推荐用户手动复制内容再分析。
- 个人数据采集需要授权：微信读书和其他个人平台只能处理用户自己的数据，不能替代平台导出或合规审查。

一个不告诉你边界在哪的阅读工具，不值得信任。

## 参考

Read Buddy 汇集并整理了多个信息获取、内容读取、转写、翻译、摘要和个人数据采集 Skill。其中播客链路整合了 [SpaceZephyr/onepod-Skill](https://github.com/SpaceZephyr/onepod-Skill) 的 YouTube / 小宇宙处理能力，微信读书链路整合了 [SpaceZephyr/space-weread](https://github.com/SpaceZephyr/space-weread) 的导出、分析和回顾能力。

其中部分 Skill 依赖 Chrome CDP、Feishu Open API、YouTube transcript、OCR API、RSS feed、Playwright 或本地脚本，具体依赖以各目录的 `SKILL.md` 和 `scripts/` 为准。

## 许可证

MIT
