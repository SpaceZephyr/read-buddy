#!/bin/bash
# 小宇宙播客转文字脚本（改编自 agent-reach）
# 用法: bash transcribe.sh [--polish] <小宇宙链接> [输出文件路径]
# 环境变量: GROQ_API_KEY (必须)
#
# --polish: 转录后调用 Groq Llama 3.3 70B 给文稿补中文标点+合理分段
#           （Whisper 对中文标点支持较弱，开启后阅读体验显著更好）
#
# 流程：抓音频直链 → 下载 → 转码压缩 → 按时长切片 → Groq Whisper 转录 → 清洗 → 合并输出

set -e

# ~/.local/bin 常用于放静态版 ffmpeg/ffprobe（macOS 上 brew 不可用时），自动纳入 PATH
export PATH="$HOME/.local/bin:$PATH"
# 强制 UTF-8 locale，否则 wc -m 等会报 "Illegal byte sequence"（无条件覆盖，防止继承到 C）
export LC_ALL=en_US.UTF-8 LANG=en_US.UTF-8

# 依赖检查：缺哪个直接报清楚，别等到中途才失败
MISSING=""
for bin in curl perl python3 ffmpeg ffprobe; do
    command -v "$bin" >/dev/null 2>&1 || MISSING="$MISSING $bin"
done
if [ -n "$MISSING" ]; then
    echo "❌ 缺少依赖：$MISSING" >&2
    echo "   ffmpeg/ffprobe 安装：macOS 用 'brew install ffmpeg'；" >&2
    echo "   若 brew 不可用，可下载静态二进制放到 ~/.local/bin（见 README）。" >&2
    exit 1
fi

POLISH=0
while [ $# -gt 0 ]; do
    case "$1" in
        --polish) POLISH=1; shift ;;
        --) shift; break ;;
        -h|--help)
            echo "用法: bash transcribe.sh [--polish] <小宇宙链接> [输出文件路径]"
            exit 0 ;;
        --*)
            echo "未知选项: $1" >&2
            exit 1 ;;
        *) break ;;
    esac
done

URL="${1:?用法: bash transcribe.sh [--polish] <小宇宙链接> [输出文件路径]}"
OUTPUT="${2:-/tmp/podcast_transcript.txt}"
TMPDIR="/tmp/xiaoyuzhou_$$"

GROQ_API_KEY="${GROQ_API_KEY:?请先设置环境变量：export GROQ_API_KEY=gsk_xxxxx（免费申请：https://console.groq.com）}"

# Groq API 限制: 25MB per file
MAX_CHUNK_SIZE_MB=20
# Whisper 内部按 16kHz 处理，故压到 16kHz/单声道/32k 即可：文件更小、上传与转录都更快，
# 能显著降低 Groq 返回 524（处理超时）的概率。
AUDIO_RATE="16000"
AUDIO_BITRATE="32k"
SEGMENT_SECONDS=600   # 每段 10 分钟，避免单段过长导致 Whisper 524 超时

cleanup() { rm -rf "$TMPDIR"; }
trap cleanup EXIT
mkdir -p "$TMPDIR"

echo "📻 小宇宙播客转文字"
echo "===================="

# Step 1: 提取音频直链和标题（小宇宙把音频 CDN 直链写在页面 HTML 里，无需登录/API）
echo "🔍 正在解析页面..."
PAGE=$(curl -s -A "Mozilla/5.0" "$URL")
AUDIO_URL=$(echo "$PAGE" | perl -ne 'while (/(https:\/\/media\.xyzcdn\.net\/[^"]*\.(?:m4a|mp3))/gi) { print "$1\n" }' | head -1)
TITLE=$(echo "$PAGE" | perl -ne 'if (/"title":"([^"]*)"/) { print "$1\n"; last }' | head -1)

if [ -z "$AUDIO_URL" ]; then
    echo "❌ 无法从页面提取音频链接（请确认是单集页面 xiaoyuzhoufm.com/episode/xxx）"
    exit 1
fi

echo "📝 标题: $TITLE"
echo "🔗 音频: $AUDIO_URL"

# Step 2: 下载音频
echo "⬇️  正在下载音频..."
EXT="${AUDIO_URL##*.}"
EXT="${EXT%%\?*}"   # 去掉可能的 query string
curl -fsL -A "Mozilla/5.0" --retry 5 --retry-delay 2 -C - -o "$TMPDIR/original.$EXT" "$AUDIO_URL"
echo "📦 文件大小: $(ls -lh "$TMPDIR/original.$EXT" | awk '{print $5}')"

# Step 3: 获取时长
DURATION=$(ffprobe -v quiet -show_entries format=duration -of csv=p=0 "$TMPDIR/original.$EXT" 2>/dev/null | cut -d. -f1)
DURATION=${DURATION:-0}
DURATION_MIN=$((DURATION / 60))
DURATION_SEC=$((DURATION % 60))
echo "⏱️  时长: ${DURATION_MIN}分${DURATION_SEC}秒"

# Step 4: 转为低码率单声道 MP3
echo "🔄 正在转码..."
ffmpeg -y -i "$TMPDIR/original.$EXT" -vn -ac 1 -ar "$AUDIO_RATE" -b:a "$AUDIO_BITRATE" "$TMPDIR/mono.mp3" 2>/dev/null
MONO_SIZE=$(stat -f%z "$TMPDIR/mono.mp3" 2>/dev/null || stat -c%s "$TMPDIR/mono.mp3")
echo "📦 转码后: $((MONO_SIZE / 1024 / 1024))MB"

# Step 5: 按时长切片（固定 10 分钟/段）
# 注意：必须按时长切，不能切太长。单段过长 Groq Whisper 会处理超时返回 524。
# 10 分钟 @ 64k 单声道 ≈ 4.8MB，远低于 25MB 限制，且单次请求快、不易超时。
MAX_BYTES=$((MAX_CHUNK_SIZE_MB * 1024 * 1024))
if [ "$MONO_SIZE" -le "$MAX_BYTES" ] && [ "$DURATION" -le "$SEGMENT_SECONDS" ]; then
    cp "$TMPDIR/mono.mp3" "$TMPDIR/chunk_000.mp3"
    NUM_CHUNKS=1
    echo "📎 无需切片"
else
    echo "✂️  按每 $((SEGMENT_SECONDS / 60)) 分钟切片..."
    # re-encode 切片（而非 -c copy），保证每段在切点处干净、可独立解码
    ffmpeg -y -loglevel error -i "$TMPDIR/mono.mp3" \
        -f segment -segment_time "$SEGMENT_SECONDS" \
        -ac 1 -ar "$AUDIO_RATE" -b:a "$AUDIO_BITRATE" "$TMPDIR/chunk_%03d.mp3"
    NUM_CHUNKS=$(ls "$TMPDIR"/chunk_*.mp3 2>/dev/null | wc -l | tr -d ' ')
    echo "   共 $NUM_CHUNKS 段"
fi
# 收集 chunk 文件列表（按文件名排序）
CHUNKS=()
while IFS= read -r f; do CHUNKS+=("$f"); done < <(ls "$TMPDIR"/chunk_*.mp3 | sort)

# Whisper 在静音/音乐段常产生的幻觉噪声，转录后清洗掉。
# 用 Python（UTF-8 安全；perl 字节模式会切坏中文多字节字符）。
# 正则刻意"有界"，绝不用 [^。]* 这类贪婪跨度，避免误删正文。
clean_transcript() {
    python3 - "$1" <<'PY'
import re, sys
p = sys.argv[1]
t = open(p, encoding="utf-8", errors="replace").read()
NOISE = [
    r"[\s.，。、]*Amara\.org\s*社区提供",                 # 先清 Amara 字幕标记
    r"(?:这个)?字幕由[\s\w.]{0,15}?社区提供",
    r"请不吝点赞[\s，、,]*订阅[\s，、,]*转发[\s，、,]*打赏支持[^\n，。]{0,12}",
    r"请输出包含[^\n]{0,40}?的转写文本[。．]?",
    r"感谢(?:大家)?(?:的)?(?:收看|观看|聆听|收听|支持)[，。]?",
    r"[※★]+",
]
for pat in NOISE:
    t = re.sub(pat, "", t)
open(p, "w", encoding="utf-8").write(t)
PY
}

# Step 6: 调用 Groq Whisper API 转录
echo "🎙️  正在转录 (Groq Whisper large-v3)..."
PROMPT="以下是一段中文普通话播客录音，请输出包含完整中文标点（，。？！：；""''）的转写文本。"

transcribe_one() {
    curl -s --max-time 600 -w "\n%{http_code}" \
        https://api.groq.com/openai/v1/audio/transcriptions \
        -H "Authorization: Bearer $GROQ_API_KEY" \
        -F file="@$1" \
        -F model="whisper-large-v3" \
        -F language="zh" \
        -F prompt="$PROMPT" \
        -F response_format="text"
}

i=0
for chunk in "${CHUNKS[@]}"; do
    i=$((i + 1))
    echo -n "   段 $i/$NUM_CHUNKS... "
    # 最多尝试 4 次：429 按提示等待，5xx/网络错误指数退避重试
    ATTEMPT=0
    while :; do
        ATTEMPT=$((ATTEMPT + 1))
        # || true 防止 curl 超时/网络错误(exit!=0) 被 set -e 直接杀死，交给重试逻辑处理
        RESPONSE=$(transcribe_one "$chunk") || true
        HTTP_CODE=$(printf '%s' "$RESPONSE" | tail -1)
        BODY=$(printf '%s' "$RESPONSE" | sed '$d')
        [ "$HTTP_CODE" = "200" ] && break
        if [ "$ATTEMPT" -ge 5 ]; then
            echo "❌ API 错误 (HTTP ${HTTP_CODE:-超时/网络}，已重试 $ATTEMPT 次)"; echo "$BODY"; exit 1
        fi
        if [ "$HTTP_CODE" = "429" ]; then
            WAIT_SEC=$(echo "$BODY" | perl -ne 'if (/in (\d+)m/) { print "$1\n"; exit }')
            WAIT_SEC=${WAIT_SEC:-2}
            WAIT_SEC=$((WAIT_SEC * 60 + 30))
            echo -n "⏳ 限流等 ${WAIT_SEC}s... "
        else
            WAIT_SEC=$((ATTEMPT * 15))
            echo -n "⚠️  HTTP $HTTP_CODE，${WAIT_SEC}s 后重试... "
        fi
        sleep "$WAIT_SEC"
    done
    TFILE="$TMPDIR/transcript_$(printf '%03d' $((i-1))).txt"
    printf '%s' "$BODY" > "$TFILE"
    clean_transcript "$TFILE"
    echo "✅ ($(wc -m < "$TFILE") 字)"
done

# Step 6.5 (可选): 用 Llama 3.3 70B 给文稿补标点+分段（只加标点，不改字）
if [ "$POLISH" = "1" ]; then
    echo "✨ 正在润色（Llama 3.3 70B 加标点+分段）..."
    for i in $(seq 0 $((NUM_CHUNKS - 1))); do
        IDX=$(printf '%03d' "$i")
        echo -n "   段 $((i+1))/$NUM_CHUNKS... "
        IN_FILE="$TMPDIR/transcript_${IDX}.txt" \
        OUT_FILE="$TMPDIR/polished_${IDX}.txt" \
        GROQ_API_KEY="$GROQ_API_KEY" \
        python3 <<'PY'
import json, os, sys, ssl, urllib.request, urllib.error
KEY = os.environ["GROQ_API_KEY"]; IN = os.environ["IN_FILE"]; OUT = os.environ["OUT_FILE"]
MODEL = "llama-3.3-70b-versatile"; MAX_DEPTH = 3
# macOS 自带/python.org 的 Python 常缺 CA 根证书 → SSL CERTIFICATE_VERIFY_FAILED。
# 优先用 certifi 的证书，没有就退回不校验，保证润色能跑通。
try:
    import certifi
    SSL_CTX = ssl.create_default_context(cafile=certifi.where())
except Exception:
    SSL_CTX = ssl._create_unverified_context()
PROMPT_TMPL = (
    "以下是一段中文普通话播客的语音转写片段，由于 Whisper 对中文标点支持较弱，"
    "整段几乎没有标点。请你**只做一件事**：在合适位置补充中文标点（，。！？：；），"
    "可以适度分段。\n\n**严格要求**：\n- 不得修改、删除、增加任何汉字或英文/数字\n"
    "- 不得改写、润色、总结\n- 不得添加任何解释、前言、后记\n- 直接输出加好标点+合理分段后的全文\n\n原文：\n{}"
)
def call_groq(text):
    body = json.dumps({"model": MODEL, "temperature": 0.2, "max_completion_tokens": 8192,
        "messages": [{"role": "user", "content": PROMPT_TMPL.format(text)}]}).encode()
    req = urllib.request.Request("https://api.groq.com/openai/v1/chat/completions", data=body,
        headers={"Authorization": f"Bearer {KEY}", "Content-Type": "application/json",
                 "User-Agent": "read-xiaoyuzhou-article/1.0"})
    with urllib.request.urlopen(req, timeout=180, context=SSL_CTX) as r:
        resp = json.load(r)
    return resp["choices"][0]["message"]["content"].strip(), resp["choices"][0].get("finish_reason")
def polish(text, depth=0):
    try:
        out, fr = call_groq(text)
    except Exception as e:
        sys.stderr.write(f"polish error: {e}\n"); return text
    if fr != "length" or depth >= MAX_DEPTH:
        return out
    mid = len(text) // 2
    return polish(text[:mid], depth + 1) + polish(text[mid:], depth + 1)
content = open(IN, encoding="utf-8", errors="replace").read().strip()
open(OUT, "w", encoding="utf-8").write(polish(content) + "\n")
print(f"✅ ({len(open(OUT, encoding='utf-8').read())} 字)")
PY
    done
fi

# Step 7: 合并输出
echo "📄 正在合并文字稿..."
{
    echo "# $TITLE"
    echo ""
    echo "来源: $URL"
    echo "时长: ${DURATION_MIN}分${DURATION_SEC}秒"
    echo "转录时间: $(date '+%Y-%m-%d %H:%M')"
    [ "$POLISH" = "1" ] && echo "润色: Groq Llama 3.3 70B"
    echo ""
    echo "---"
    echo ""
    for i in $(seq 0 $((NUM_CHUNKS - 1))); do
        IDX=$(printf '%03d' "$i")
        if [ "$POLISH" = "1" ] && [ -f "$TMPDIR/polished_${IDX}.txt" ]; then
            cat "$TMPDIR/polished_${IDX}.txt"
        else
            cat "$TMPDIR/transcript_${IDX}.txt"
        fi
        echo ""
    done
} > "$OUTPUT"

echo ""
echo "✅ 转录完成！"
echo "📄 文稿: $OUTPUT"
echo "📊 总字数: $(wc -m < "$OUTPUT")"
echo "===================="
