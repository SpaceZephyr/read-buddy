#!/usr/bin/env python3
"""Convert a Markdown file to PDF via headless Chrome.

Usage: python3 md_to_pdf.py input.md output.pdf
"""
import sys
import os
import subprocess
import tempfile
import re
from pathlib import Path

CHROME_PATHS = [
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/Applications/Chromium.app/Contents/MacOS/Chromium",
    "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
    "/Applications/Arc.app/Contents/MacOS/Arc",
]

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<title>{title}</title>
<style>
  @page {{ size: A4; margin: 18mm 16mm; }}
  body {{
    font-family: -apple-system, "PingFang SC", "Hiragino Sans GB", "Microsoft YaHei", serif;
    font-size: 11pt;
    line-height: 1.7;
    color: #1a1a1a;
    max-width: 720px;
    margin: 0 auto;
  }}
  h1 {{
    font-size: 22pt;
    border-bottom: 2px solid #1a1a1a;
    padding-bottom: 8px;
    margin-top: 0;
  }}
  h2 {{
    font-size: 16pt;
    margin-top: 32px;
    border-left: 4px solid #c9a96e;
    padding-left: 10px;
  }}
  h3 {{
    font-size: 13pt;
    color: #555;
    margin-top: 22px;
  }}
  blockquote {{
    border-left: 3px solid #c9a96e;
    background: #faf7f0;
    margin: 12px 0;
    padding: 10px 16px;
    color: #333;
    border-radius: 0 4px 4px 0;
  }}
  hr {{
    border: none;
    border-top: 1px dashed #ccc;
    margin: 28px 0;
  }}
  p {{ margin: 8px 0; }}
  strong {{ color: #1a1a1a; }}
  a {{ color: #1a1a1a; text-decoration: none; border-bottom: 1px solid #ccc; }}
  ul, ol {{ padding-left: 24px; }}
  li {{ margin: 4px 0; }}
  code {{
    background: #f3f3f3;
    padding: 2px 6px;
    border-radius: 3px;
    font-size: 0.9em;
  }}
</style>
</head>
<body>
{body}
</body>
</html>
"""


def md_to_html(md_text: str) -> str:
    try:
        import markdown
        return markdown.markdown(md_text, extensions=["extra", "toc", "sane_lists"])
    except ImportError:
        pass
    return naive_md(md_text)


def naive_md(t: str) -> str:
    lines = t.split("\n")
    out = []
    in_quote = False
    for line in lines:
        if line.startswith("# "):
            out.append(f"<h1>{line[2:]}</h1>")
        elif line.startswith("## "):
            out.append(f"<h2>{line[3:]}</h2>")
        elif line.startswith("### "):
            out.append(f"<h3>{line[4:]}</h3>")
        elif line.startswith("---"):
            out.append("<hr>")
        elif line.startswith("> "):
            if not in_quote:
                out.append("<blockquote>")
                in_quote = True
            out.append(line[2:].strip() + "<br>")
        elif line.strip() == "":
            if in_quote:
                out.append("</blockquote>")
                in_quote = False
            out.append("<p></p>")
        else:
            if in_quote:
                out.append("</blockquote>")
                in_quote = False
            line = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", line)
            out.append(f"<p>{line}</p>")
    if in_quote:
        out.append("</blockquote>")
    return "\n".join(out)


def find_chrome() -> str | None:
    for p in CHROME_PATHS:
        if os.path.exists(p):
            return p
    return None


def main():
    if len(sys.argv) != 3:
        print("Usage: md_to_pdf.py input.md output.pdf", file=sys.stderr)
        sys.exit(1)

    md_path = Path(sys.argv[1]).resolve()
    pdf_path = Path(sys.argv[2]).resolve()

    if not md_path.exists():
        print(f"Markdown not found: {md_path}", file=sys.stderr)
        sys.exit(1)

    chrome = find_chrome()
    if not chrome:
        print("Chrome/Chromium not found. Install Google Chrome or pass --skip-pdf.", file=sys.stderr)
        sys.exit(2)

    md_text = md_path.read_text(encoding="utf-8")
    title = md_path.stem
    body = md_to_html(md_text)
    html = HTML_TEMPLATE.format(title=title, body=body)

    with tempfile.NamedTemporaryFile("w", suffix=".html", delete=False, encoding="utf-8") as f:
        f.write(html)
        html_path = f.name

    try:
        subprocess.run(
            [
                chrome,
                "--headless",
                "--disable-gpu",
                "--no-sandbox",
                f"--print-to-pdf={pdf_path}",
                "--print-to-pdf-no-header",
                f"file://{html_path}",
            ],
            check=True,
            capture_output=True,
        )
        print(f"PDF written: {pdf_path}")
    finally:
        os.unlink(html_path)


if __name__ == "__main__":
    main()
