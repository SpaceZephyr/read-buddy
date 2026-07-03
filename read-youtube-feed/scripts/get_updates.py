#!/usr/bin/env python3
"""
获取关注的 YouTube 博主最近更新
用法: python get_updates.py [--days 2]
"""

import requests
import re
from datetime import datetime, timedelta
import argparse
import json

# 关注的 YouTube 频道列表 (来自 Zara's AI Learning Library)
# 格式: (名称, channel_id, 频道URL)
CHANNELS = [
    # === AI 教育 & 技术深度 ===
    ("Andrej Karpathy", "UCXUPKJO5MZQN11PqgIvyuvQ", "@AndrejKarpathy"),
    ("Anthropic", "UCrDwWp7EBBv4NwvScIpBDOA", "@anthropic-ai"),
    ("Lex Fridman", "UCGwuxdEeCf0TIA2RbPOj-8g", "@lexfridman"),
    
    # === AI 产品 & 创业 ===
    ("Lenny's Podcast", "UCcIXPgBDgKd5EbfWi4i5cVA", "@LennysPodcast"),
    ("Peter Yang", "UCSHZKyawb77ixDdsGog4iWA", "@PeterYangYT"),
    ("The MAD Podcast (Matt Turck)", "UCQID78IY6EOojr5RUdD47MQ", "@DataDrivenNYC"),
    ("Every", "UCXZFVVCFahewxr3est7aT7Q", "@EveryInc"),
    
    # === VC & 投资人 ===
    ("Y Combinator", "UCcefcZRL2oaA_uBNeo5UOWg", "@ycombinator"),
    ("Latent Space", "UCwBTFE_6Bsb_EtmXlW2aTlg", "@LatentSpacePod"),
    ("South Park Commons", "UCnpBg7yqNauHtlNSpOl5-cg", "@southparkcommons"),
    ("No Priors", "UC4Snw5yrSDMXys31I18U3gg", "@NoPriorsPodcast"),
    ("a16z", "UCE_b6sxLv68tda7tvv5YWuA", "@a16z"),
    
    # === 大厂 & 研究 ===
    ("Google DeepMind", "UCP7jMXSY2xbc3KCAE0MHQ-A", "@googledeepmind"),
    ("Google for Developers", "UC_x5XG1OV2P6uZZ5FSM9Ttw", "@GoogleDevelopers"),
    ("Stanford GSB", "UCjIMtrzxYc0lblGhmOgC_CA", "@stanfordgsb"),
    
    # === Vibe Coding & 工具 ===
    ("Mckay Wrigley", "UCbGt-LT2R9hglFeTr6KuXkw", "@realmckaywrigley"),
    ("Tiago Forte", "UCxBcwypKK-W3GHd_RZ9FZrQ", "@TiagoForte"),
    ("The Pragmatic Engineer", "UCWG5I2nL7zyrRj6bCy5qC7A", "@ThePragmaticEngineer"),
    
    # === AI 新闻 & 趋势 ===
    ("The AI Daily Brief", "UCIAtPXNxXPKmw-_1sYnrJzQ", "@TheAIDailyBrief"),
    ("TBPN", "UCQvWX73GQygcwXOTSf_VDVg", "@TBPNLive"),
    ("Brett Malinowski", "UCMR-rPSUI34DRQXUkvFuIUQ", "@TheBrettWay"),

    # === 投资 & 商业访谈 ===
    ("Invest Like the Best", "UCpQBb0fToph3jrDulwz1iUQ", "@ILTB_Podcast"),
    ("The All-In Podcast", "UCESLZhusAkFfsNsApnjF_Cg", "@allin"),
    ("Acquired", "UCyFqFYfTW2VoIQKylJ04Rtw", "@AcquiredFM"),
    ("CNBC Television", "UCvJJ_dzjViJCoLf5uKUTwoA", "@CNBCtelevision"),

    # === 深度访谈 ===
    ("Dwarkesh Patel", "UCZa18YV7qayTh-MRIrBhDpA", "@DwarkeshPatel"),
    ("Core Memory (Ashlee Vance)", "UCzWnSedVeqUyze_R6M5BqwA", "@CoreMemoryVideos"),
    ("Joseph Noel Walker", "UCQ5Rjt_Vcy8D1ineFBY4y_Q", "@josephnoelwalker"),
    ("The Information Bottleneck", "UCFPYHur5LvervD60Aba-9cw", "@information_bottleneck"),

    # === 写作 & 思考 ===
    ("How I Write (David Perell)", "UC0a_pO439rhcyHBZq3AKdrw", "@DavidPerellChannel"),

    # === 健康 & 科学 ===
    ("Huberman Lab", "UC2D2CMWXMOVWx7giW1n3LIg", "@hubermanlab"),
]


BROWSER_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36',
    'Accept-Language': 'en-US,en;q=0.9',
    'Cookie': 'CONSENT=YES+1; PREF=hl=en&gl=US',
}


def fetch_channel_page(handle):
    """抓取 @handle/videos 页面 HTML"""
    h = handle.lstrip('@')
    url = f"https://www.youtube.com/@{h}/videos"
    try:
        response = requests.get(url, headers=BROWSER_HEADERS, timeout=15)
        if response.status_code == 200:
            return response.text
    except Exception as e:
        print(f"获取频道页失败 {handle}: {e}")
    return None


_RELATIVE_RE = re.compile(r'(\d+)\s+(second|minute|hour|day|week|month|year)s?\s+ago', re.IGNORECASE)
_UNIT_DAYS = {
    'second': 0, 'minute': 0, 'hour': 0,
    'day': 1, 'week': 7, 'month': 30, 'year': 365,
}


def parse_relative_time(text):
    """将 'N units ago' 字符串转换为发布日期。无法解析返回 None。"""
    if not text:
        return None
    m = _RELATIVE_RE.search(text)
    if not m:
        return None
    n = int(m.group(1))
    unit = m.group(2).lower()
    days_ago = n * _UNIT_DAYS.get(unit, 0)
    return datetime.now() - timedelta(days=days_ago)


def parse_channel_page(html, channel_name, days=2):
    """从频道页 ytInitialData 中提取最近 N 天的视频"""
    videos = []
    if not html:
        return videos
    m = re.search(r'var ytInitialData = (\{.*?\});</script>', html)
    if not m:
        return videos
    try:
        data = json.loads(m.group(1))
    except Exception as e:
        print(f"解析 ytInitialData 失败 {channel_name}: {e}")
        return videos

    tabs = data.get('contents', {}).get('twoColumnBrowseResultsRenderer', {}).get('tabs', [])
    items = []
    for tab in tabs:
        tr = tab.get('tabRenderer', {})
        if tr.get('selected') and tr.get('title', '').lower() == 'videos':
            items = tr.get('content', {}).get('richGridRenderer', {}).get('contents', [])
            break

    cutoff = datetime.now() - timedelta(days=days)
    for it in items:
        lv = it.get('richItemRenderer', {}).get('content', {}).get('lockupViewModel', {})
        if not lv:
            continue
        video_id = lv.get('contentId')
        if not video_id:
            continue
        md = lv.get('metadata', {}).get('lockupMetadataViewModel', {})
        title = md.get('title', {}).get('content', 'Unknown')

        # metadata rows 通常是 [views, published]
        rows = md.get('metadata', {}).get('contentMetadataViewModel', {}).get('metadataRows', [])
        meta_parts = []
        for r in rows:
            for p in r.get('metadataParts', []):
                txt = p.get('text', {}).get('content')
                if txt:
                    meta_parts.append(txt)

        views = None
        published_text = None
        for part in meta_parts:
            if 'ago' in part.lower():
                published_text = part
            elif 'view' in part.lower():
                views = part

        pub_date = parse_relative_time(published_text)
        if pub_date is None or pub_date < cutoff:
            continue

        # duration
        duration = None
        ci = lv.get('contentImage', {}).get('thumbnailViewModel', {})
        for ov in ci.get('overlays', []):
            for b in ov.get('thumbnailBottomOverlayViewModel', {}).get('badges', []):
                tb = b.get('thumbnailBadgeViewModel', {})
                if tb.get('text'):
                    duration = tb['text']

        videos.append({
            'channel': channel_name,
            'title': title,
            'video_id': video_id,
            'published': pub_date.strftime('%Y-%m-%d %H:%M'),
            'published_text': published_text or '',
            'url': f"https://www.youtube.com/watch?v={video_id}",
            'description': '',
            'views': views or '',
            'duration': duration or '',
        })
    return videos


def fetch_video_description(video_id):
    """从视频页提取描述（用于摘要生成）"""
    try:
        url = f"https://www.youtube.com/watch?v={video_id}"
        response = requests.get(url, headers=BROWSER_HEADERS, timeout=10)
        if response.status_code != 200:
            return ''
        m = re.search(r'ytInitialPlayerResponse\s*=\s*(\{.*?\});', response.text, re.DOTALL)
        if m:
            try:
                data = json.loads(m.group(1))
                desc = data.get('videoDetails', {}).get('shortDescription', '')
                return desc[:1500]
            except Exception:
                pass
    except Exception:
        pass
    return ''


def get_video_details(video_id):
    """获取视频详情：播放数和时长"""
    result = {'views': None, 'duration': None}
    try:
        url = f"https://www.youtube.com/watch?v={video_id}"
        headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36', 'Cookie': 'CONSENT=YES+1'}
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            import re
            def extract_details(text):
                views_value = None
                duration_seconds = None

                player_match = re.search(r'ytInitialPlayerResponse\s*=\s*(\{.*?\});', text, re.DOTALL)
                if player_match:
                    try:
                        player_data = json.loads(player_match.group(1))
                        video_details = player_data.get('videoDetails', {})
                        views_value = video_details.get('viewCount')
                        duration_seconds = video_details.get('lengthSeconds')
                    except Exception:
                        pass

                if views_value is None:
                    match = re.search(r'"viewCount":"(\d+)"', text)
                    if match:
                        views_value = match.group(1)

                if views_value is None:
                    match = re.search(r'"viewCountText":\{"simpleText":"([^"]+)"\}', text)
                    if match:
                        views_value = match.group(1)

                if duration_seconds is None:
                    duration_match = re.search(r'"lengthSeconds":"(\d+)"', text)
                    if duration_match:
                        duration_seconds = duration_match.group(1)

                return views_value, duration_seconds

            views_value, duration_seconds = extract_details(response.text)

            if views_value is None or duration_seconds is None:
                alt_url = f"https://r.jina.ai/https://www.youtube.com/watch?v={video_id}"
                alt_response = requests.get(alt_url, headers=headers, timeout=10)
                if alt_response.status_code == 200:
                    alt_views, alt_duration = extract_details(alt_response.text)
                    if views_value is None:
                        views_value = alt_views
                    if duration_seconds is None:
                        duration_seconds = alt_duration

            if views_value is None or duration_seconds is None:
                key_match = re.search(r'INNERTUBE_API_KEY\":\"([^\"]+)\"', text)
                context_match = re.search(r'INNERTUBE_CONTEXT\":(\{.*?\})\s*,\s*\"INNERTUBE_CONTEXT_CLIENT_NAME\"', text, re.DOTALL)
                if key_match and context_match:
                    try:
                        key = key_match.group(1)
                        context = json.loads(context_match.group(1))
                        payload = {"context": context, "videoId": video_id}
                        api_url = f"https://www.youtube.com/youtubei/v1/player?key={key}"
                        api_response = requests.post(api_url, json=payload, headers=headers, timeout=10)
                        if api_response.status_code == 200:
                            api_data = api_response.json()
                            api_details = api_data.get('videoDetails', {})
                            if views_value is None:
                                views_value = api_details.get('viewCount')
                            if duration_seconds is None:
                                duration_seconds = api_details.get('lengthSeconds')
                    except Exception:
                        pass

            if views_value is not None:
                digits = re.sub(r'[^\d]', '', str(views_value))
                if digits:
                    views = int(digits)
                    if views >= 1000000:
                        result['views'] = f"{views/1000000:.1f}M"
                    elif views >= 1000:
                        result['views'] = f"{views/1000:.1f}K"
                    else:
                        result['views'] = str(views)

            if duration_seconds is not None:
                seconds = int(duration_seconds)
                hours = seconds // 3600
                minutes = (seconds % 3600) // 60
                if hours > 0:
                    result['duration'] = f"{hours}h{minutes:02d}m"
                else:
                    result['duration'] = f"{minutes}分钟"
    except:
        pass
    return result


def generate_summary(description, title, max_chars=400):
    """从描述中提取摘要，默认 400 字"""
    if not description:
        return f"关于「{title}」的最新视频内容，点击链接观看完整视频。"
    
    # 清理描述文本
    lines = description.split('\n')
    clean_lines = []
    for line in lines:
        line = line.strip()
        # 跳过链接行、订阅提示、空行、时间戳
        if not line:
            continue
        if line.startswith('http') or line.startswith('Subscribe') or line.startswith('→'):
            continue
        if 'subscribe' in line.lower() or 'goo.gle' in line.lower():
            continue
        if line.startswith('0:') or line.startswith('1:') or line.startswith('2:'):  # 跳过时间戳
            continue
        if line.startswith('#') and len(line) < 30:  # 跳过短标签
            continue
        clean_lines.append(line)
    
    # 合并成摘要
    summary = ' '.join(clean_lines)
    
    # 截取到合适长度，保持句子完整
    if len(summary) > max_chars:
        # 尝试在句号、问号、感叹号处截断
        for end_char in ['。', '！', '？', '. ', '! ', '? ', '— ', ': ']:
            pos = summary[:max_chars].rfind(end_char)
            if pos > max_chars * 0.6:  # 至少保留 60% 内容
                return summary[:pos+1]
        # 否则直接截断
        return summary[:max_chars] + '...'
    
    return summary if summary else f"关于「{title}」的最新视频内容，点击链接观看完整视频。"


def main():
    parser = argparse.ArgumentParser(description='获取关注的 YouTube 博主最近更新')
    parser.add_argument('--days', type=int, default=2, help='获取最近 N 天的更新 (默认: 2)')
    parser.add_argument('--json', action='store_true', help='以 JSON 格式输出')
    parser.add_argument('--markdown', action='store_true', help='以 Markdown 格式输出')
    parser.add_argument('--views', action='store_true', help='获取播放量（会增加请求时间）')
    args = parser.parse_args()
    
    all_videos = []
    
    import sys
    print(f"正在获取最近 {args.days} 天的播客更新...", file=sys.stderr)
    
    for name, channel_id, handle in CHANNELS:
        html = fetch_channel_page(handle)
        if html:
            videos = parse_channel_page(html, name, args.days)
            all_videos.extend(videos)

    # 按发布时间排序
    all_videos.sort(key=lambda x: x['published'], reverse=True)

    # 抓取描述用于摘要（仅在窗口内的视频，数量有限）
    print(f"正在抓取 {len(all_videos)} 个视频的描述...", file=sys.stderr)
    import time
    for video in all_videos:
        video['description'] = fetch_video_description(video['video_id'])
        video['summary'] = generate_summary(video['description'], video['title'])
        time.sleep(0.2)
    
    if args.json:
        print(json.dumps(all_videos, ensure_ascii=False, indent=2))
    elif args.markdown:
        # Markdown 格式输出
        if not all_videos:
            print(f"最近 {args.days} 天没有新的播客更新。")
            return
        
        print(f"## 📺 最近 {args.days} 天共有 {len(all_videos)} 个新播客更新\n")
        
        for i, video in enumerate(all_videos, 1):
            date_short = video['published'].split(' ')[0][5:]  # MM-DD
            duration_str = f" | ⏱ {video.get('duration')}" if video.get('duration') else ""
            views_str = f" | 👁 {video.get('views')}" if video.get('views') else ""
            print(f"### {i}. [{video['title']}]({video['url']})")
            print(f"**{video['channel']}** | {date_short}{duration_str}{views_str}\n")
            print(f"> {video['summary']}\n")
            print("---\n")
    else:
        # 默认格式输出
        if not all_videos:
            print(f"最近 {args.days} 天没有新的播客更新。")
            return
        
        print(f"\n📺 最近 {args.days} 天共有 {len(all_videos)} 个新播客更新：\n")
        print("=" * 70)
        
        for i, video in enumerate(all_videos, 1):
            date_short = video['published'].split(' ')[0][5:]  # MM-DD
            duration_str = f" | ⏱ {video.get('duration')}" if video.get('duration') else ""
            views_str = f" | 👁 {video.get('views')}" if video.get('views') else ""
            print(f"\n{i}. 【{video['channel']}】{date_short}{duration_str}{views_str}")
            print(f"   📌 {video['title']}")
            print(f"   🔗 {video['url']}")
            print(f"   📝 {video['summary']}")
            print("-" * 70)


if __name__ == "__main__":
    main()
