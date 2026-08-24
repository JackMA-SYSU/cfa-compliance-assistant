# -*- coding: utf-8 -*-
"""RAG 引擎测试：输出结构与字段完整性"""
import pytest


def test_analyze_returns_valid_structure(engine):
    r = engine.analyze("客户送我去打高尔夫并承担差旅费")
    assert r["risk_level"] in {"high", "mid", "low"}
    assert isinstance(r["risk_score"], float)
    assert isinstance(r["standards"], list)
    assert isinstance(r["checklist"], list)
    assert isinstance(r["referenced_cases"], list)
    assert isinstance(r["processing_time_ms"], int)


def test_high_risk_has_disclosure(engine):
    r = engine.analyze("客户在公司薪酬之外额外给我一笔奖金")
    if r["risk_level"] == "high":
        assert r["disclosure_draft"], "高风险行为应提供披露草稿"


def test_checklist_items_have_ids(engine):
    r = engine.analyze("我的个人账户提前买入股票")
    for i, c in enumerate(r["checklist"]):
        assert c["id"] == i + 1
        assert c["text"]


def test_cache_returns_same_result(engine):
    text = "客户送我去看高尔夫球比赛"
    r1 = engine.analyze(text)
    r2 = engine.analyze(text)
    assert r1["risk_level"] == r2["risk_level"]
    assert r1["category"] == r2["category"]


def test_retrieval_finds_relevant_case(engine, kb):
    cases = kb.search("客户请我吃饭还要承担我出差的酒店费用", top_k=3)
    assert len(cases) > 0
    # 至少命中一个与招待/差旅相关的案例
    tags = [t for c in cases for t in c.get("behavior_tags", [])]
    assert "gift_entertainment" in tags, "应检索到招待类案例"
