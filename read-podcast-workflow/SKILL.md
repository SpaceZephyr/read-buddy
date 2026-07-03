---
name: read-podcast-workflow
description: |
  播客处理一站式工作流。支持两种入口：
  (1) 直接处理：提供 YouTube 链接，直接进入处理流程
  (2) 更新检查：获取关注博主的最新更新，用户挑选后处理
  功能：字幕提取 → read-content-digest 处理 → 自动保存飞书知识库。
  触发词："获取播客更新"、"处理这个播客"、"播客工作流"、"有什么新播客"。
---

# 播客处理工作流

从 YouTube 到飞书发布的一站式播客处理流程。

## 两种入口

### 入口 A：获取播客更新（推荐）

用户说"获取播客更新"或"有什么新播客"时：

```
获取更新 → 展示列表 → 用户选择 → 字幕提取 → [询问] → Content-Digest → 飞书
```

### 入口 B：直接处理链接

用户提供 YouTube 链接时：

```
YouTube 链接 → 字幕提取 → [询问] → Content-Digest → 飞书
```

## 入口 A：获取播客更新流程

### Step A1: 获取更新列表

**运行命令：**
```bash
python3 /Users/ugreen/.claude/skills/read-youtube-feed/scripts/get_updates.py --days 2
```

**输出格式：**
```
📺 最近 2 天共有 N 个新播客更新：

1. 【Lenny's Podcast】
   📌 视频标题
   🕐 2026-01-30 15:00
   🔗 https://www.youtube.com/watch?v=xxx
   📝 简要描述...

2. 【No Priors】
   ...
```

### Step A2: 用户选择

展示列表后询问：
```
请选择要处理的播客（输入序号，如 1 或 1,3），或输入 "跳过"：
```

等待用户选择后，进入 Step 1。

---

## 入口 B：直接处理流程

### Step 1: 提取 YouTube 字幕

**运行命令：**
```bash
python3 /Users/ugreen/.claude/skills/read-youtube-transcript/scripts/get_transcript.py "YOUTUBE_URL"
```

**输出**：Markdown 格式的字幕文本

### Step 2: 询问是否处理

字幕提取成功后，**必须询问用户**：

```
字幕提取成功！是否使用 read-content-digest 处理成精华内容？
- 处理后会生成：标题 + 核心观点列表 + 精华片段
- 处理完成后自动保存到飞书「每日播客推荐」
```

**等待用户确认后再继续**。

### Step 3: Content-Digest 处理

参考 `/Users/ugreen/.claude/skills/read-content-digest/SKILL.md` 的完整流程。

**关键格式要求（v2 — 2026-05-12 更新）：**

每篇播客摘要使用如下统一格式，**所有字段都必须填写**：

```markdown
文章标题：MMDD-文章中文一句话主题（如 0512-如何搭建个人 AI OS）
嘉宾：[嘉宾名]（Twitter @handle）
频道：[频道名]
日期：YYYY-MM-DD
主题：[一句话主题描述，30 字内]
播客地址：[YouTube 完整 URL]

# 核心观点

1、[观点]。[完整的逻辑阐述，包含推理过程，2-4 句话]

2、[观点]。[完整的逻辑阐述，包含推理过程，2-4 句话]

...（10-15 条）

# 精彩片段

[使用 Style B 对话式访谈格式，挑选 3-5 个最精彩的片段，保留嘉宾原话翻译]
```

**字段说明：**
- `文章标题`：用作飞书文档的标题和本地文件名前缀，格式 `MMDD-中文一句话主题`
- `嘉宾`：如果能查到 Twitter 账号附上，查不到就只写名字
- `日期`：视频在 YouTube 的发布日期，不是处理日期
- `主题`：一句话能让人决定要不要看的描述

### Step 4: 保存到本地

**保存位置：** `/Users/ugreen/Documents/obsidian/每日播客/`

**文件命名：** `MMDD-嘉宾名-主题关键词.md`

示例：`0130-Peter-Steinberger-AI编程革命.md`

### Step 5: 自动保存到飞书

**运行命令：**
```bash
python3 /Users/ugreen/.claude/skills/feishu-wiki/scripts/save_to_wiki.py \
  --file "/Users/ugreen/Documents/obsidian/每日播客/MMDD-xxx.md" \
  --title "MMDD：嘉宾名 X 栏目名：一句话观点" \
  --parent "TOSJwKzxTiFdiRk0aducHNBFntg"
```

**父节点 Token：** `TOSJwKzxTiFdiRk0aducHNBFntg`（每日播客推荐）

### Step 6: 返回结果并询问图片

处理完成后，向用户展示：

```
✅ 播客处理完成！

📝 本地文件：/Users/ugreen/Documents/obsidian/每日播客/MMDD-xxx.md
📤 飞书文档：https://my.feishu.cn/wiki/xxx

核心观点数：N 条
精华片段数：N 个

---

是否要将核心观点转为图片海报？（适合小红书/朋友圈分享）
```

### Step 7: 转换为图片（可选）

如果用户确认要转为图片，调用 `markdown-to-image` Skill：

1. **提取短文版本**：只保留标题 + 核心观点列表（不含精华片段）
2. **优化格式**：
   - 添加 emoji 序号（1️⃣ 2️⃣ 3️⃣）
   - 精简每条观点到 1-2 句话
   - 控制总字数在 500 字以内
3. **使用浏览器 MCP 操作 Madopic**：
   - 打开 https://madopic.thus.chat
   - 粘贴优化后的 Markdown
   - 选择模式（小红书 3:4 或朋友圈长图）
   - 导出 PNG
4. **告知用户图片已下载到下载目录**

## 快速使用示例

**用户说：**
> 处理这个播客 https://www.youtube.com/watch?v=xxxxx

**Agent 执行：**
1. 提取字幕 ✓
2. 询问用户 → 用户确认
3. Content-Digest 处理 ✓
4. 保存本地 ✓
5. 保存飞书 ✓
6. 返回结果

## 错误处理

| 错误 | 处理方式 |
|------|---------|
| 字幕提取失败 | 告知用户视频可能没有字幕，询问是否手动提供文本 |
| 飞书写入失败 | 检查权限，提示用户添加应用到知识库协作者 |
| 网络超时 | 重试一次，仍失败则告知用户 |

## 关注的 YouTube 频道

数据来源：[Zara's AI Learning Library](https://zara.faces.site/ai)

| 分类 | 频道 |
|-----|------|
| AI 教育 | Andrej Karpathy, Anthropic, Lex Fridman |
| AI 产品 | Lenny's Podcast, Peter Yang, The MAD Podcast, Every |
| VC 投资 | Y Combinator, Latent Space, South Park Commons, No Priors, a16z |
| 大厂研究 | Google DeepMind, Google for Developers, Stanford GSB |
| Vibe Coding | Mckay Wrigley, Tiago Forte, The Pragmatic Engineer |
| AI 新闻 | The AI Daily Brief, TBPN, Brett Malinowski |

**共 21 个频道**

添加新频道：编辑 `/Users/ugreen/.claude/skills/read-youtube-feed/scripts/get_updates.py`

## 依赖的 Skills

- `read-youtube-feed`：获取博主更新
- `read-youtube-transcript`：字幕提取
- `read-content-digest`：内容处理
- `feishu-wiki`：飞书写入
- `markdown-to-image`：转换为图片海报（可选）

## 配置

| 配置项 | 值 |
|--------|-----|
| 本地保存路径 | `/Users/ugreen/Documents/obsidian/每日播客/` |
| 飞书父节点 | `TOSJwKzxTiFdiRk0aducHNBFntg`（每日播客推荐） |
| 观点数量 | 10-15 条 |
| 更新检查天数 | 2 天 |
