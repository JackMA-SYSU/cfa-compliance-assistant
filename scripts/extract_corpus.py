# -*- coding: utf-8 -*-
"""从 raw_pdf_text.txt 提取结构化题库，输出 ethics_corpus.jsonl"""
import re
import json
import os

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(BASE, "data", "raw_pdf_text.txt")
OUT = os.path.join(BASE, "data", "ethics_corpus.jsonl")

# CFA 准则代码 -> 中文名称 + 必做动作 + 行为类别 + 默认风险
STANDARD_MAP = {
    "I(A)": ("法律认知", "遵守适用法律法规；向监管者报告违法行为", "research_integrity", "mid"),
    "I(B)": ("独立性与客观性", "拒绝可能损害独立客观性的礼品、招待或好处", "gift_entertainment", "high"),
    "I(C)": ("虚假陈述", "不得作出虚假陈述或遗漏重大事实；纠正错误信息", "research_integrity", "high"),
    "I(D)": ("不当行为", "不得从事欺诈、欺骗等有损职业声誉的行为", "conflict_interest", "high"),
    "II(A)": ("重大非公开信息", "不得利用或促使他人利用重大非公开信息", "mnpi", "high"),
    "II(B)": ("市场操纵", "不得操纵市场价格或成交量", "research_integrity", "high"),
    "III(A)": ("忠诚、审慎与谨慎", "以客户利益为先；审慎管理客户资产", "conflict_interest", "mid"),
    "III(B)": ("公平交易", "公平客观对待所有客户", "conflict_interest", "mid"),
    "III(C)": ("适当性", "投资行动前了解客户需求、目标与风险承受能力", "conflict_interest", "mid"),
    "III(D)": ("业绩陈述", "确保业绩陈述公平、准确、完整", "research_integrity", "mid"),
    "III(E)": ("保密", "对客户及前雇主信息保密", "leaving_job", "mid"),
    "IV(A)": ("对雇主的忠诚", "不得剥夺雇主技能优势；避免利益冲突", "leaving_job", "mid"),
    "IV(B)": ("额外报酬安排", "向雇主书面披露并取得所有相关方书面同意", "extra_compensation", "high"),
    "IV(C)": ("监督者责任", "建立合规程序；监督下属行为", "conflict_interest", "mid"),
    "V(A)": ("勤勉与合理依据", "基于充分研究与合理依据提出建议", "research_integrity", "mid"),
    "V(B)": ("与客户沟通", "区分事实与观点；披露分析方法与风险", "research_integrity", "mid"),
    "V(C)": ("记录保存", "保存支持投资决策与建议的记录", "research_integrity", "low"),
    "VI(A)": ("利益冲突披露", "充分披露影响独立性的利益冲突", "conflict_interest", "high"),
    "VI(B)": ("交易优先顺序", "客户交易优先于个人交易；禁止抢先交易", "personal_trade", "high"),
    "VI(C)": ("介绍费", "披露并取得相关方同意后收取介绍费", "extra_compensation", "mid"),
    "VII(A)": ("CFA项目参与者行为", "遵守考试规则；不得泄露考题内容", "research_integrity", "low"),
    "VII(B)": ("CFA头衔引用", "按规范引用CFA协会会员资格与头衔", "research_integrity", "low"),
}

STD_RE = re.compile(r"(?:VII|VI|IV|III|II|V|I)\([A-E]\)")


def clean(s):
    return re.sub(r"\s+", " ", s or "").strip()


def extract_block(block):
    """从单个题目文本块提取字段"""
    qid_m = re.match(r"(M\d-Q\d+)", block)
    if not qid_m:
        return None
    qid = qid_m.group(1)
    module = qid.split("-")[0]
    rest = block[qid_m.end():]

    # 头部：题目类别/标准代码/作答状态
    header = ""
    status = "当时未作答"
    wrong_choice = None
    h_end = rest.find("E N G L I S H")
    if h_end == -1:
        h_end = rest.find("对照")
    header_line = rest[:h_end] if h_end != -1 else rest[:200]
    header = clean(header_line)
    if "当时做错" in header:
        status = "当时做错"
        wm = re.search(r"错选\s*([A-C])", header)
        if wm:
            wrong_choice = wm.group(1)
    elif "当时做对" in header:
        status = "当时做对"

    # 英文情景
    scenario_en = ""
    scenario_cn = ""
    eng_idx = rest.find("E N G L I S H")
    cn_idx = rest.find("对照")
    opt_idx = rest.find("项English")
    if opt_idx == -1:
        opt_idx = rest.find("答案")
    if eng_idx != -1:
        en_start = eng_idx + len("E N G L I S H")
        en_end = cn_idx if cn_idx != -1 else (opt_idx if opt_idx != -1 else len(rest))
        scenario_en = clean(rest[en_start:en_end])
    scenario_en = re.sub(r"中[⽂文]?\s*$", "", scenario_en)
    if cn_idx != -1:
        cn_start = cn_idx + len("对照")
        cn_end = opt_idx if opt_idx != -1 else len(rest)
        scenario_cn = clean(rest[cn_start:cn_end])
    scenario_cn = re.sub(r"\s*选\s*$", "", scenario_cn)

    # 选项与正确答案
    options = {}
    correct_answer = None
    am = re.search(r"答案\s*Answer\s*[:：]\s*([A-C])", rest)
    if am:
        correct_answer = am.group(1)
    # 解析选项：每个选项以行首 A/B/C 开头，捕获到下一个选项或"答案"为止
    opt_section = rest[opt_idx:] if opt_idx != -1 else rest
    ans_in = opt_section.find("答案")
    if ans_in != -1:
        opt_section = opt_section[:ans_in]
    marks = list(re.finditer(r"(?m)^\s*([A-C])\b", opt_section))
    for i, m in enumerate(marks):
        letter = m.group(1)
        end = marks[i + 1].start() if i + 1 < len(marks) else len(opt_section)
        text = clean(opt_section[m.start():end])
        text = re.sub(r"^[A-C]\s*✓?\s*", "", text)
        options[letter] = text

    # 解析 + 做题方法
    explanation = ""
    method = ""
    exp_idx = rest.find("解析")
    if exp_idx != -1:
        meth_idx = rest.find("做题", exp_idx)
        exp_end = meth_idx if meth_idx != -1 else len(rest)
        explanation = clean(rest[exp_idx + 2:exp_end])
        if meth_idx != -1:
            method = clean(rest[meth_idx + 2:])
            method = re.sub(r"^[⽅方]法\s*", "", method)
            method = clean(re.split(r"=====", method)[0])

    # 标准代码（头部 + 解析里提取；排除干扰项"X 错"部分）
    correct_part = re.split(r"\s*[A-C]\s*错", explanation)[0]
    codes = STD_RE.findall(header + " " + correct_part)
    if not codes:
        codes = STD_RE.findall(header + " " + explanation)
    # 去重保序
    seen = set()
    std_codes = []
    for c in codes:
        if c not in seen:
            seen.add(c)
            std_codes.append(c)

    return {
        "question_id": qid,
        "module": module,
        "standard_code": std_codes,
        "scenario_en": scenario_en,
        "scenario_cn": scenario_cn,
        "correct_answer": correct_answer,
        "options": options,
        "explanation": explanation,
        "method": method,
        "answer_status": status,
        "wrong_choice": wrong_choice,
        "header": header,
    }


def enrich(rec):
    """补充 behavior_tags / risk_level / required_actions / standard_name"""
    codes = rec["standard_code"]
    names = []
    actions = []
    cats = set()
    risk = "low"
    for c in codes:
        info = STANDARD_MAP.get(c)
        if not info:
            continue
        name, action, cat, lvl = info
        names.append(f"{c} {name}")
        if action:
            actions.append(action)
        cats.add(cat)
        if lvl == "high":
            risk = "high"
        elif lvl == "mid" and risk != "high":
            risk = "mid"
    # 行为标签：类别 + 关键词
    tags = list(cats)
    text = (rec["scenario_cn"] or "") + (rec["explanation"] or "")
    for kw, cat in [
        ("礼", "gift_entertainment"), ("招待", "gift_entertainment"), ("差旅", "gift_entertainment"),
        ("兼职", "side_job"), ("副业", "side_job"), ("授课", "side_job"),
        ("离职", "leaving_job"), ("跳槽", "leaving_job"), ("创业", "leaving_job"),
        ("个人交易", "personal_trade"), ("抢先", "personal_trade"),
        ("额外报酬", "extra_compensation"), ("介绍费", "extra_compensation"),
        ("研报", "research_integrity"), ("评级", "research_integrity"),
        ("非公开", "mnpi"), ("内幕", "mnpi"),
        ("冲突", "conflict_interest"), ("持股", "conflict_interest"), ("董事", "conflict_interest"),
    ]:
        if kw in text:
            tags.append(cat)
    rec["standard_name"] = names
    rec["required_actions"] = actions
    rec["behavior_tags"] = sorted(set(tags))
    rec["risk_level"] = risk
    # 类似关键词扩展（基础）
    rec["similar_keywords"] = sorted(set(tags)) + [c for c in codes]
    return rec


def main():
    text = open(RAW, encoding="utf-8").read()
    # 去掉页码前缀干扰：分块
    blocks = re.split(r"(?=M\d-Q\d+)", text)
    records = []
    for b in blocks:
        rec = extract_block(b)
        if rec is None:
            continue
        if not rec["scenario_cn"] and not rec["scenario_en"]:
            continue
        rec = enrich(rec)
        records.append(rec)

    with open(OUT, "w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    print(f"解析完成: {len(records)} 题")
    from collections import Counter
    mods = Counter(r["module"] for r in records)
    print("模块分布:", dict(sorted(mods.items())))
    empty_cn = sum(1 for r in records if not r["scenario_cn"])
    empty_en = sum(1 for r in records if not r["scenario_en"])
    no_std = sum(1 for r in records if not r["standard_code"])
    print(f"中文情景为空: {empty_cn}, 英文情景为空: {empty_en}, 无标准代码: {no_std}")


if __name__ == "__main__":
    main()
