# -*- coding: utf-8 -*-
"""CFA 七大准则 22 子条款定义（用于速查与 LLM Prompt 构建）"""

STANDARDS = {
    "I(A)": {"name": "法律认知", "desc": "遵守所有适用法律法规；对可疑违法行为向监管者报告并采取合理行动。"},
    "I(B)": {"name": "独立性与客观性", "desc": "保持职业判断的独立客观，不接受可能损害独立性的礼品、招待或好处。"},
    "I(C)": {"name": "虚假陈述", "desc": "不得在投资分析、建议或执业活动中作出虚假陈述或遗漏重大事实。"},
    "I(D)": {"name": "不当行为", "desc": "不得从事欺诈、欺骗等有损职业诚信与声誉的不当行为。"},
    "II(A)": {"name": "重大非公开信息", "desc": "不得利用重大非公开信息交易，也不得促使他人据此行事；需采取措施防止信息滥用。"},
    "II(B)": {"name": "市场操纵", "desc": "不得从事扭曲市场价格或成交量的操纵行为，不得散布虚假误导信息。"},
    "III(A)": {"name": "忠诚、审慎与谨慎", "desc": "以客户利益为先，审慎管理客户资产；行使代理投票等权利时独立判断。"},
    "III(B)": {"name": "公平交易", "desc": "在提供投资分析、建议和交易时公平客观对待所有客户。"},
    "III(C)": {"name": "适当性", "desc": "采取投资行动前，了解客户需求、目标、财务状况与风险承受能力，在整体组合语境下判断适当性。"},
    "III(D)": {"name": "业绩陈述", "desc": "确保投资业绩陈述公平、准确、完整。"},
    "III(E)": {"name": "保密", "desc": "对当前、潜在及前客户的机密信息保密，除非法律或调查要求披露。"},
    "IV(A)": {"name": "对雇主的忠诚", "desc": "在雇佣相关事务中不得剥夺雇主的技能与能力优势；不得因个人利益损害雇主。"},
    "IV(B)": {"name": "额外报酬安排", "desc": "接受与雇主利益相竞争的额外报酬前，须向雇主书面披露并取得所有相关方书面同意。"},
    "IV(C)": {"name": "监督者责任", "desc": "监督者须合理防范下属违反法律法规与准则，建立合规程序并督促执行。"},
    "V(A)": {"name": "勤勉与合理依据", "desc": "基于充分的研究与合理的依据作出投资分析与建议，保持勤勉。"},
    "V(B)": {"name": "与客户沟通", "desc": "与客户沟通时区分事实与观点，披露分析方法、风险与重要限制。"},
    "V(C)": {"name": "记录保存", "desc": "保存支持投资决策、建议与行动的研究记录，并遵守记录保存要求。"},
    "VI(A)": {"name": "利益冲突披露", "desc": "充分披露所有可能损害独立客观或妨碍履职的利益冲突（持股、董事职务等）。"},
    "VI(B)": {"name": "交易优先顺序", "desc": "客户交易优先于本人及雇主交易；禁止抢先交易、禁止利用客户订单牟利。"},
    "VI(C)": {"name": "介绍费", "desc": "收取或支付介绍费须向雇主、客户及潜在客户披露，并取得相关方同意。"},
    "VII(A)": {"name": "CFA项目参与者行为", "desc": "遵守考试规则，不得泄露考试内容，不得提供或接受考试协助。"},
    "VII(B)": {"name": "CFA头衔引用", "desc": "按规范引用 CFA 协会会员资格、CFA 头衔及候选身份，不得误导。"},
}

# 8 大行为类别 -> 中文名 + 涉及准则簇
CATEGORY_STANDARDS = {
    "gift_entertainment": ["I(B)", "IV(B)", "VI(A)"],
    "side_job": ["IV(A)", "IV(B)", "VI(A)"],
    "leaving_job": ["IV(A)", "III(E)"],
    "personal_trade": ["VI(B)", "II(A)"],
    "extra_compensation": ["IV(B)", "VI(C)"],
    "research_integrity": ["V(A)", "V(B)", "I(C)"],
    "mnpi": ["II(A)"],
    "conflict_interest": ["VI(A)", "I(B)"],
    "misconduct": ["I(D)"],
}

CATEGORY_NAMES = {
    "gift_entertainment": "收礼/招待/差旅",
    "side_job": "兼职/副业/外部授课",
    "leaving_job": "离职/跳槽/创业",
    "personal_trade": "个人账户交易/抢先交易",
    "extra_compensation": "额外报酬/介绍费",
    "research_integrity": "研报/评级/虚假陈述",
    "mnpi": "内幕信息/泄密",
    "conflict_interest": "利益冲突/持股/董事职务",
    "misconduct": "不当行为/专业失德",
}

RISK_LEVEL_TEXT = {
    "high": "高风险：涉及需书面披露或事先同意的事项，可能违反准则并导致纪律处分",
    "mid": "中风险：需要履行披露或审慎义务，操作不当可能违规",
    "low": "低风险：属于常规执业行为，注意保持合规即可",
}


def standard_info(code):
    """返回 {code, name, description}"""
    info = STANDARDS.get(code)
    if not info:
        return {"code": code, "name": "", "description": ""}
    return {"code": code, "name": info["name"], "description": info["desc"]}
