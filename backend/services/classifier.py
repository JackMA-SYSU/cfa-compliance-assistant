# -*- coding: utf-8 -*-
"""Phase 1.3 — 轻量级意图识别规则引擎

基于关键词 + 正则 + 排除词的规则匹配，规则未命中时回退到 Embedding
语义相似度（与知识库 Top-3 案例比较）。置信度低于阈值返回 "uncertain"。

8 大行为类别（每类对应一个准则簇）：
    gift_entertainment   收礼/招待/差旅      -> I(B), IV(B), VI(A)
    side_job             兼职/副业/外部授课   -> IV(A), IV(B), VI(A)
    leaving_job          离职/跳槽/创业       -> IV(A), III(E)
    personal_trade       个人账户交易/抢先    -> VI(B), II(A)
    extra_compensation   额外报酬/介绍费      -> IV(B), VI(C)
    research_integrity   研报/评级/虚假陈述   -> V(A), V(B), I(C)
    mnpi                 内幕信息/泄密        -> II(A)
    conflict_interest    利益冲突/持股/董事   -> VI(A), I(B)
"""
import re

CATEGORIES = {
    "gift_entertainment": {
        "name": "收礼/招待/差旅",
        "standards": ["I(B)", "IV(B)", "VI(A)"],
        "keywords": [
            "礼品", "礼物", "赠礼", "送礼", "收礼", "馈赠", "好处",
            "招待", "宴请", "请客", "吃饭", "聚餐", "餐饮", "娱乐",
            "差旅", "旅行", "旅游", "机票", "酒店", "住宿", "报销",
            "高尔夫", "球票", "门票", "演唱会", "赛事", "度假",
            "免费", "会议费", "专属活动", "礼品卡", "优惠",
        ],
        "regex": [
            r"(收|接受|赠送|赠与|安排)[^，。]{0,12}(礼品|礼物|招待|差旅|旅游|门票|高尔夫|住宿)",
            r"(差旅|旅行|住宿|餐饮)[^，。]{0,8}(费用|报销|由.{0,6}承担)",
        ],
        "negative": ["客户资料", "数据", "报告", "分析"],
    },
    "side_job": {
        "name": "兼职/副业/外部授课",
        "standards": ["IV(A)", "IV(B)", "VI(A)"],
        "keywords": [
            "兼职", "副业", "私活", "第二职业", "兼职工作", "外部授课",
            "授课", "讲课", "讲座", "培训", "演讲", "顾问", "咨询",
            "外部董事会", "非雇主", "业余", "额外工作", "外聘",
        ],
        "regex": [
            r"(兼职|副业|授课|讲座|顾问)[^，。]{0,10}(收入|报酬|费|酬劳)",
            r"(非|外部|雇主以外)[^，。]{0,8}(公司|机构|董事|职位)",
        ],
        "negative": ["内部培训", "本职工作"],
    },
    "leaving_job": {
        "name": "离职/跳槽/创业",
        "standards": ["IV(A)", "III(E)"],
        "keywords": [
            "离职", "跳槽", "辞职", "创业", "换工作", "离开公司",
            "新雇主", "新公司", "离职后", "辞职后", "带走客户",
            "客户名单", "挖角", "竞争对手", "竞业", "交接", "离职期",
        ],
        "regex": [
            r"(离职|辞职|跳槽|离开)[^，。]{0,12}(前|后|时|期间)",
            r"(带走|索取|复制)[^，。]{0,8}(客户|名单|资料|模型)",
        ],
        "negative": [],
    },
    "personal_trade": {
        "name": "个人账户交易/抢先交易",
        "standards": ["VI(B)", "II(A)"],
        "keywords": [
            "个人交易", "个人账户", "自己的账户", "本人账户", "亲属账户",
            "抢先交易", "front running", "先于客户", "抢在客户前",
            "自营", "个人投资", "私人投资", "同日交易", "提前下单",
        ],
        "regex": [
            r"(个人|本人|自己|亲属|配偶)[^，。]{0,8}(账户|交易|买卖)",
            r"(先于|抢在|提前)[^，。]{0,8}(客户|下单|交易)",
        ],
        "negative": [],
    },
    "extra_compensation": {
        "name": "额外报酬/介绍费",
        "standards": ["IV(B)", "VI(C)"],
        "keywords": [
            "额外报酬", "额外补偿", "额外收入", "介绍费", "推荐费",
            "业绩奖励", "业绩提成", "奖金", "回扣", "好处费", "佣金",
            "客户赠与", "报酬安排", "薪酬之外", "额外支付", "馈赠现金",
        ],
        "regex": [
            r"(额外|薪酬之外|工资之外)[^，。]{0,10}(报酬|补偿|收入|奖励|费)",
            r"(介绍费|推荐费|回扣|好处费)[^，。]{0,10}(收取|支付|给予)",
        ],
        "negative": ["拒绝"],
    },
    "research_integrity": {
        "name": "研报/评级/虚假陈述",
        "standards": ["V(A)", "V(B)", "I(C)"],
        "keywords": [
            "研报", "研究报告", "评级", "推荐", "预测", "目标价",
            "虚假陈述", "误导", "夸大", "遗漏", "不实", "编造",
            "合理依据", "尽职调查", "模型", "假设", "数据错误",
            "复制报告", "署名", "发表", "观点", "事实",
        ],
        "regex": [
            r"(研报|报告|评级|推荐|预测)[^，。]{0,10}(虚假|误导|夸大|遗漏|不实)",
            r"(发表|发布|署名)[^，。]{0,8}(研报|报告|推荐|评级)",
        ],
        "negative": ["个人"],
    },
    "mnpi": {
        "name": "内幕信息/泄密",
        "standards": ["II(A)"],
        "keywords": [
            "内幕", "内幕信息", "非公开", "重大非公开", "未公开信息",
            "机密", "泄密", "泄露", "内部消息", "小道消息", "传闻",
            "未披露", "并购消息", "重大消息", "知情", "透露",
        ],
        "regex": [
            r"(内幕|非公开|未公开|机密|内部)[^，。]{0,6}(信息|消息|数据)",
            r"(泄露|透露|告知)[^，。]{0,8}(信息|消息|内容)",
        ],
        "negative": [],
    },
    "conflict_interest": {
        "name": "利益冲突/持股/董事职务",
        "standards": ["VI(A)", "I(B)"],
        "keywords": [
            "利益冲突", "冲突", "持股", "持有股票", "股权", "股份",
            "董事", "董事会", "董事职务", "关联方", "关联交易",
            "亲属", "家人", "配偶", "朋友", "客户关系", "潜在冲突",
            "双重身份", "个人关系", "供应商",
        ],
        "regex": [
            r"(持有|购买)[^，。]{0,8}(股票|股权|股份)",
            r"(董事|监事|高管|顾问)[^，。]{0,8}(职务|兼任|任职)",
        ],
        "negative": ["无", "没有", "不存在"],
    },
    "misconduct": {
        "name": "不当行为/专业失德",
        "standards": ["I(D)"],
        "keywords": [
            "骂", "辱骂", "侮辱", "威胁", "恐吓", "打架", "斗殴", "贿赂",
            "行贿", "受贿", "欺诈", "欺骗", "舞弊", "挪用", "侵吞", "侵占",
            "盗用", "骚扰", "性骚扰", "歧视", "造假", "做假", "伪造",
            "泄露隐私", "泄漏隐私", "粗口", "不尊重",
        ],
        "regex": [
            r"(辱骂|侮辱|威胁|恐吓|欺诈|欺骗|舞弊|挪用|侵吞|骚扰|歧视|造假|伪造)[^，。]{0,8}",
        ],
        "negative": [],
    },
}


class RuleBasedClassifier:
    """8 类行为意图分类器"""

    def __init__(self, kb=None):
        self.kb = kb  # 可选：语义回退用

    def _rule_match(self, text):
        """规则匹配：返回 (best_category, score, matched_rules)"""
        text = text or ""
        best_cat, best_score, best_rules = None, 0, []
        for cat, cfg in CATEGORIES.items():
            score = 0
            rules = []
            # 排除词命中则降权
            neg_hit = sum(1 for n in cfg["negative"] if n in text)
            # 关键词命中
            for kw in cfg["keywords"]:
                if kw in text:
                    score += 1
                    rules.append(f"kw:{kw}")
            # 正则命中
            for pat in cfg["regex"]:
                if re.search(pat, text):
                    score += 2
                    rules.append(f"re:{pat}")
            score = max(0, score - neg_hit * 1.5)
            if score > best_score:
                best_cat, best_score, best_rules = cat, score, rules
        return best_cat, best_score, best_rules

    def classify(self, text, top_cases=None):
        """
        分类主入口。
        返回: {category, confidence, matched_rules, top_cases}
        """
        text = text or ""
        cat, score, rules = self._rule_match(text)

        # 规则命中
        if cat and score > 0:
            # 置信度：命中越多越高，封顶 0.95
            confidence = min(0.95, 0.55 + score * 0.08)
            return {
                "category": cat,
                "confidence": round(confidence, 3),
                "matched_rules": rules,
                "top_cases": top_cases or [],
            }

        # 语义回退：用知识库 Top-3 案例的标签投票
        if self.kb is not None:
            cases = self.kb.search(text, top_k=3)
            top_sim = cases[0].get("similarity", 0.0) if cases else 0.0
            # 相似度过低视为无关输入，返回 uncertain
            if top_sim >= 0.40:
                votes = {}
                for c in cases:
                    for tag in c.get("behavior_tags", []):
                        if tag in CATEGORIES:
                            votes[tag] = votes.get(tag, 0) + c.get("similarity", 0)
                if votes:
                    best = max(votes, key=votes.get)
                    conf = round(min(0.6, 0.3 + top_sim * 0.4), 3)
                    return {
                        "category": best,
                        "confidence": conf,
                        "matched_rules": [f"semantic:{best}"],
                        "top_cases": cases,
                    }

        return {
            "category": "uncertain",
            "confidence": 0.0,
            "matched_rules": [],
            "top_cases": top_cases or [],
        }
