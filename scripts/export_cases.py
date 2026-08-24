# -*- coding: utf-8 -*-
"""导出合规案例数据到前端，用于无后端场景下的浏览器端案例引用。

输出 frontend/js/cases.js，内容为 window.CASES = [...]
"""
import json
import os

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CORPUS = os.path.join(BASE, "data", "ethics_corpus.jsonl")
OUT = os.path.join(BASE, "frontend", "js", "cases.js")


def main():
    recs = []
    with open(CORPUS, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                recs.append(json.loads(line))

    # 只保留含明确准则代码的合规案例
    cases = [r for r in recs if r.get("standard_code")]
    out = []
    for r in cases:
        out.append({
            "id": r["question_id"],
            "module": r.get("module", ""),
            "standard_code": r.get("standard_code", []),
            "standard_name": r.get("standard_name", []),
            "risk_level": r.get("risk_level", "low"),
            "behavior_tags": r.get("behavior_tags", []),
            "required_actions": r.get("required_actions", []),
            "summary": (r.get("scenario_cn", "") or "")[:140],
        })

    payload = "window.CASES = " + json.dumps(out, ensure_ascii=False, indent=1) + ";\n"
    with open(OUT, "w", encoding="utf-8") as f:
        f.write(payload)
    print(f"已导出 {len(out)} 个案例到 frontend/js/cases.js")


if __name__ == "__main__":
    main()
