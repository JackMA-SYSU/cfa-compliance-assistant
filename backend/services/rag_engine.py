# -*- coding: utf-8 -*-
"""RAG 引擎：意图分类 -> 向量检索 -> Prompt 构建 -> LLM 生成 -> 结构化输出

LLM 输出解析失败或无 API Key 时，自动回退到本地规则引擎（离线可用）。
内置 LRU 缓存：相同输入直接返回缓存结果。
"""
import hashlib
import json
import os
import sys
import time
from collections import OrderedDict

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config  # noqa: E402
from services import standards as std  # noqa: E402
from services.llm_client import LLMClient, parse_json_output  # noqa: E402

PROMPT_TEMPLATE = """你是一位资深 CFA 合规官。基于以下信息，分析员工行为的合规风险。

【员工行为描述】
{behavior}

【行为类别】
{category}

【可能涉及的准则】
{standards}

【类似历史案例】
{retrieved_cases}

请只输出 JSON 对象（不要输出任何其他文字），格式如下：
{{
  "risk_level": "high|mid|low",
  "risk_reasoning": "风险判断理由（2-3句话）",
  "standards": [{{"code": "IV(B)", "name": "额外报酬安排", "requirement": "..."}}],
  "checklist": ["必须完成的动作1", "动作2"],
  "action_advice": "具体操作建议",
  "disclosure_draft": "给合规部门的书面披露草稿"
}}
"""

RISK_SCORE = {"high": 0.9, "mid": 0.6, "low": 0.3}


class RAGEngine:
    def __init__(self, kb, classifier, llm_client=None):
        self.kb = kb
        self.classifier = classifier
        self.llm = llm_client or LLMClient()
        self._cache = OrderedDict()
        self._cache_capacity = config.CACHE_CAPACITY

    # ---------- 缓存 ----------
    def _cache_key(self, text):
        return hashlib.md5(text.strip().encode("utf-8")).hexdigest()

    def _cache_get(self, text):
        key = self._cache_key(text)
        if key in self._cache:
            self._cache.move_to_end(key)
            return self._cache[key]
        return None

    def _cache_put(self, text, result):
        key = self._cache_key(text)
        self._cache[key] = result
        self._cache.move_to_end(key)
        while len(self._cache) > self._cache_capacity:
            self._cache.popitem(last=False)

    # ---------- 主流程 ----------
    def analyze(self, behavior):
        start = time.time()
        cached = self._cache_get(behavior)
        if cached:
            return cached

        # 1) 意图分类
        classification = self.classifier.classify(behavior)
        category = classification["category"]

        # 2) 向量检索 Top-K 案例
        cases = self.kb.search(behavior, top_k=config.RETRIEVAL_TOP_K)

        # 3) LLM 生成（失败回退规则引擎）
        result = None
        if self.llm.api_key or self.llm.base_url:
            try:
                result = self._llm_analyze(behavior, classification, cases)
            except Exception as e:  # noqa: BLE001
                print(f"[RAG] LLM 生成失败，回退规则引擎: {e}")
        if result is None:
            result = self._rule_analyze(behavior, classification, cases)

        result["processing_time_ms"] = int((time.time() - start) * 1000)
        self._cache_put(behavior, result)
        return result

    # ---------- LLM 路径 ----------
    def _llm_analyze(self, behavior, classification, cases):
        standards_text = self._standards_text(classification, cases)
        cases_text = self._cases_text(cases)
        prompt = PROMPT_TEMPLATE.format(
            behavior=behavior,
            category=std.CATEGORY_NAMES.get(classification["category"], classification["category"]),
            standards=standards_text,
            retrieved_cases=cases_text,
        )
        resp = self.llm.chat_completion(
            [{"role": "user", "content": prompt}], json_mode=True
        )
        data = parse_json_output(resp["content"])
        if not data:
            return None

        standards = []
        for s in data.get("standards", []):
            code = s.get("code", "")
            standards.append({
                "code": code,
                "name": s.get("name", "") or std.standard_info(code)["name"],
                "description": s.get("requirement", "") or std.standard_info(code)["description"],
            })
        checklist = data.get("checklist", [])
        if not isinstance(checklist, list):
            checklist = [checklist]

        return self._finalize(
            behavior, classification, cases,
            risk_level=data.get("risk_level", "mid"),
            standards=standards,
            checklist=checklist,
            action_advice=data.get("action_advice", ""),
            disclosure_draft=data.get("disclosure_draft", ""),
            risk_reasoning=data.get("risk_reasoning", ""),
            offline=False,
        )

    # ---------- 规则引擎路径（离线可用） ----------
    def _rule_analyze(self, behavior, classification, cases):
        # 标准列表：类别准则簇 + 案例中出现的准则
        codes = []
        cat_codes = std.CATEGORY_STANDARDS.get(classification["category"], [])
        codes += cat_codes
        for c in cases:
            for code in c.get("standard_code", []):
                if code and code not in codes:
                    codes.append(code)

        standards = [std.standard_info(code) for code in codes if code]

        # 风险评级：案例风险加权
        risk = self._risk_from_cases(cases, classification["category"])

        # 检查清单：从案例 required_actions 聚合
        actions = []
        for c in cases:
            for a in c.get("required_actions", []):
                if a and a not in actions:
                    actions.append(a)
        if not actions:
            actions = self._default_actions(codes)
        checklist = [{"id": i + 1, "text": a, "required": True}
                     for i, a in enumerate(actions)]

        action_advice = self._build_advice(risk, actions)
        disclosure_draft = self._build_disclosure(behavior, standards, actions, risk)
        reasoning = std.RISK_LEVEL_TEXT.get(risk, "")

        return self._finalize(
            behavior, classification, cases,
            risk_level=risk, standards=standards, checklist=checklist,
            action_advice=action_advice, disclosure_draft=disclosure_draft,
            risk_reasoning=reasoning, offline=True,
        )

    # ---------- 工具函数 ----------
    def _risk_from_cases(self, cases, category):
        if not cases:
            return "mid"
        weighted = {"high": 0.0, "mid": 0.0, "low": 0.0}
        total = 0.0
        for c in cases:
            w = c.get("similarity", 0.3)
            rl = c.get("risk_level", "mid")
            if rl in weighted:
                weighted[rl] += w
            total += w
        if total == 0:
            return "mid"
        score = (weighted["high"] * 0.9 + weighted["mid"] * 0.6 + weighted["low"] * 0.3) / total
        if score >= 0.7:
            return "high"
        if score >= 0.45:
            return "mid"
        return "low"

    def _default_actions(self, codes):
        acts = []
        for code in codes:
            info = std.STANDARDS.get(code)
            if info:
                acts.append(f"遵循{code} {info['name']}要求")
        return acts[:5]

    def _build_advice(self, risk, actions):
        head = {
            "high": "该行为风险较高，请立即停止或暂停相关安排，并在接受任何利益前完成下列动作：",
            "mid": "该行为需履行审慎与披露义务，建议按以下步骤处理：",
            "low": "该行为整体风险较低，保持合规即可，注意：",
        }.get(risk, "")
        return head + "；".join(actions) + "。"

    def _build_disclosure(self, behavior, standards, actions, risk):
        if risk == "low":
            return ""
        codes = "、".join(s["code"] for s in standards)
        acts = "\n".join(f"- {a}" for a in actions)
        return (
            f"致合规部门：\n"
            f"本人就以下事项主动书面披露：{behavior}\n\n"
            f"可能涉及的准则：{codes}\n\n"
            f"拟采取的合规动作：\n{acts}\n\n"
            f"特此披露，请予以审查并留存记录。"
        )

    def _standards_text(self, classification, cases):
        lines = []
        for code in std.CATEGORY_STANDARDS.get(classification["category"], []):
            info = std.standard_info(code)
            lines.append(f"- {code} {info['name']}: {info['description']}")
        return "\n".join(lines) if lines else "（未命中具体准则）"

    def _cases_text(self, cases):
        lines = []
        for c in cases:
            code = ",".join(c.get("standard_code", []))
            lines.append(
                f"- {c['question_id']} (相似度 {c.get('similarity')}, 准则 {code}, "
                f"风险 {c.get('risk_level')}): {c.get('text', '')[:120]}"
            )
        return "\n".join(lines) if lines else "（无类似案例）"

    def _finalize(self, behavior, classification, cases, risk_level, standards,
                  checklist, action_advice, disclosure_draft, risk_reasoning, offline):
        score = RISK_SCORE.get(risk_level, 0.5)
        if not checklist:
            checklist = [{"id": 1, "text": "评估并记录该行为的合规性", "required": True}]
        if isinstance(checklist[0], str):
            checklist = [{"id": i + 1, "text": t, "required": True}
                         for i, t in enumerate(checklist)]
        referenced = [{
            "question_id": c["question_id"],
            "similarity": c.get("similarity", 0.0),
            "risk_level": c.get("risk_level", ""),
            "standard_code": c.get("standard_code", []),
            "summary": (c.get("text", "") or "")[:200],
        } for c in cases]
        return {
            "risk_level": risk_level,
            "risk_score": round(score, 2),
            "category": classification["category"],
            "confidence": classification.get("confidence", 0.0),
            "standards": standards,
            "checklist": checklist,
            "action_advice": action_advice,
            "disclosure_draft": disclosure_draft,
            "risk_reasoning": risk_reasoning,
            "referenced_cases": referenced,
            "offline": offline,
        }
