---
name: read-xiaoyuzhou-article
description: |
  把小宇宙播客链接转成文字稿和文章。实现原理：下载小宇宙音频 → Groq Whisper 转录成文字 → 由 Claude 编写成文章。
  触发词："小宇宙转文字"、"播客转文章"、"把这个小宇宙链接转成文章"、"小宇宙文稿"，或用户直接发来 xiaoyuzhoufm.com 的单集链接。
  产出两份：逐字文稿（含标点润色）+ 改写后的文章。
---

# 小宇宙播客转文章

把一条小宇宙单集链接（`xiaoyuzhoufm.com/episode/xxx`）变成：
1. **逐字文稿**（转录 + 中文标点润色）
2. **文章**（由 Claude 在文稿基础上改写成可读文章）

## 实现原理

```
小宇宙链接
  → 抓页面里的音频 CDN 直链（无需登录/API）
  → curl 下载音频
  → ffmpeg 转码压缩（单声道 64k mp3）
  → 按 10 分钟/段切片（避免单段过长导致 Whisper 524 超时）
  → Groq Whisper large-v3 转录（language=zh，带 429/5xx 自动重试）
  → 清洗 Whisper 幻觉噪声（"请点赞订阅"、"字幕由 Amara.org 提供"等）
  → Groq Llama 3.3 70B 补中文标点+分段（可选 --polish）
  → 输出逐字文稿
  → Claude 把文稿编写成文章
```

## 前置要求

**1. 工具**（命令行需可用）：`curl`、`ffmpeg`、`ffprobe`、`perl`、`python3`
- macOS 安装 ffmpeg：`brew install ffmpeg`
- 若 brew 不可用（如 Xcode 许可证未接受），可下载静态二进制放到 `~/.local/bin/`（脚本会自动把该目录加入 PATH）。arm64 静态版可从 osxexperts.net 获取 `ffmpeg`/`ffprobe`。
- 脚本启动时会自检依赖，缺哪个会直接报出来。

**2. Groq API Key（免费）**——转录这一步需要：
- 注册 https://console.groq.com 拿到 `gsk_` 开头的 key
- 设置环境变量：`export GROQ_API_KEY=gsk_xxxxx`
- 若未设置，运行脚本时会报错提示。

## 工作流程

### Step 1: 确认链接和润色选项

用户给出小宇宙单集链接后，默认开启 `--polish`（标点润色，阅读体验更好）。

### Step 2: 运行转录脚本

```bash
GROQ_API_KEY=$GROQ_API_KEY bash ~/.claude/skills/read-xiaoyuzhou-article/scripts/transcribe.sh \
  --polish "<小宇宙链接>" "/tmp/podcast_transcript.md"
```

脚本会输出逐字文稿到 `/tmp/podcast_transcript.md`。读取它作为下一步素材。

> 长播客转录可能需要几分钟（下载 + 转码 + 多段调用 API）。如遇 Groq 429 限流，脚本会自动等待重试。

### Step 3: 编写成文章

读取 `/tmp/podcast_transcript.md`，把逐字稿改写成一篇结构化文章。要求：

- **保留核心观点和关键信息**，去掉口语赘词、重复、语气词（"对对对""然后呢""那个"）
- **重新组织结构**：开头点题 → 用小标题分主题 → 结尾收束
- **忠实于原意**：不要编造文稿里没有的事实、数据、观点
- 嘉宾有金句的话可以适当引用
- 在文章开头标注来源链接和播客标题

把文章保存为 `/tmp/podcast_article.md`，并把两份产出（文稿 + 文章）路径告知用户。

## 注意事项

- 只支持小宇宙**单集页面**（`/episode/`），不支持播客主页。
- 音频直链是从页面 HTML 正则提取 `media.xyzcdn.net/*.m4a|mp3`；若小宇宙改版导致提取失败，需更新脚本里的正则。
- 转录用 Groq 免费额度，超大量使用可能触发速率限制。
- 改写文章这一步由 Claude 完成，不额外消耗 API。
