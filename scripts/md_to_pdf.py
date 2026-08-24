# -*- coding: utf-8 -*-
"""将商策报告 markdown 转为 PDF（中文友好）

流程：预处理 mermaid -> 转 HTML（带 CSS）-> Edge 无头打印为 PDF
"""
import re
import subprocess
import os
import sys

sys.stdout.reconfigure(encoding="utf-8")

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MD = os.path.join(BASE, "商策报告_B赛道.md")
HTML = os.path.join(BASE, "商策报告_临时.html")
PDF = os.path.join(BASE, "商策报告_暑假不回家队.pdf")
EDGE = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"


def mermaid_to_text(block):
    block = block.strip()
    if block.startswith("pie"):
        # pie title ... / "label" : value
        items = re.findall(r'"([^"]+)"\s*:\s*(\d+)', block)
        title_m = re.search(r'title\s+(.+)', block)
        title = title_m.group(1).strip() if title_m else ""
        lines = ["**" + title + "**"] if title else []
        total = sum(int(v) for _, v in items)
        for label, v in items:
            pct = int(v) / total * 100 if total else 0
            lines.append(f"- {label}：{v} 题（{pct:.1f}%）")
        return "\n".join(lines)
    if block.startswith("flowchart"):
        # 提取节点标签，转成文字箭头
        nodes = re.findall(r'\[([^\]]+)\]', block)
        labels = [n.split("<br>")[0].strip() for n in nodes]
        # 去重保序
        seen, out = set(), []
        for l in labels:
            if l and l not in seen:
                seen.add(l)
                out.append(l)
        return "流程：" + " → ".join(out)
    return "（图表）"


def preprocess(text):
    # 替换 mermaid 代码块
    def repl(m):
        return mermaid_to_text(m.group(1))
    text = re.sub(r"```mermaid\s*\n(.*?)```", repl, text, flags=re.S)
    return text


def main():
    text = open(MD, encoding="utf-8").read()
    text = preprocess(text)

    import markdown
    body = markdown.markdown(text, extensions=["tables", "fenced_code", "sane_lists"])

    css = """
    <style>
      @page { size: A4; margin: 2cm; }
      body { font-family: "Microsoft YaHei", "PingFang SC", sans-serif; font-size: 12pt; line-height: 1.8; color: #1f2a44; max-width: 800px; margin: 0 auto; padding: 20px; }
      h1 { color: #0e1a33; border-bottom: 3px solid #d4af37; padding-bottom: 8px; font-size: 22pt; }
      h2 { color: #0e1a33; margin-top: 24px; font-size: 16pt; border-left: 4px solid #d4af37; padding-left: 10px; }
      h3 { color: #1f3560; font-size: 13pt; }
      table { border-collapse: collapse; width: 100%; margin: 12px 0; font-size: 10.5pt; }
      th, td { border: 1px solid #d0d5e0; padding: 6px 10px; text-align: left; }
      th { background: #0e1a33; color: #fff; }
      blockquote { color: #6b7280; border-left: 3px solid #d4af37; margin: 10px 0; padding: 4px 14px; }
      code { background: #f3f5f9; padding: 1px 5px; border-radius: 3px; font-size: 10.5pt; }
      pre { background: #f3f5f9; padding: 12px; border-radius: 6px; overflow-x: auto; }
      strong { color: #0e1a33; }
      hr { border: none; border-top: 1px solid #e6e9f2; margin: 20px 0; }
    </style>
    """
    html = f"<!DOCTYPE html><html><head><meta charset='utf-8'>{css}</head><body>{body}</body></html>"
    open(HTML, "w", encoding="utf-8").write(html)

    subprocess.run([
        EDGE, "--headless", "--disable-gpu",
        f"--print-to-pdf={PDF}",
        "--no-pdf-header-footer",
        HTML,
    ], check=True, timeout=60)

    print("已生成 PDF:", PDF, "| 大小:", os.path.getsize(PDF), "bytes")


if __name__ == "__main__":
    main()
