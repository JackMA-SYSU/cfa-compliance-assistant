# -*- coding: utf-8 -*-
"""意图分类器单元测试：8 类行为 + 边界情况"""
import pytest

# 每类至少 2 个用例 + 边界
CASES = [
    ("客户送我高尔夫球票还承担差旅费", "gift_entertainment"),
    ("供应商请我去高档餐厅吃饭并安排旅行", "gift_entertainment"),
    ("我想业余时间接一份外部授课的兼职", "side_job"),
    ("朋友邀请我去另一家公司担任顾问拿报酬", "side_job"),
    ("我准备离职创业并带走客户名单", "leaving_job"),
    ("我跳槽前复制了公司的客户资料", "leaving_job"),
    ("我的个人账户提前于客户账户买入股票", "personal_trade"),
    ("我用亲属账户抢在客户前面交易", "personal_trade"),
    ("客户在公司薪酬之外额外付我一笔奖金", "extra_compensation"),
    ("我收取了推荐客户给第三方的介绍费", "extra_compensation"),
    ("我在研报里夸大了某股票的评级和预测", "research_integrity"),
    ("我复制了同事的研报署上自己的名字发表", "research_integrity"),
    ("我得知公司未公开的并购内幕消息", "mnpi"),
    ("我把非公开信息透露给朋友让他买股票", "mnpi"),
    ("我持有客户公司的股票并兼任其董事", "conflict_interest"),
    ("我的配偶持有被投公司的股权我没有披露", "conflict_interest"),
]

BOUNDARY = [
    ("今天天气不错，我想出去走走", "uncertain"),
    ("我正常履行本职工作，没有任何利益往来", "uncertain"),
]


@pytest.mark.parametrize("text,expected", CASES)
def test_category_classification(classifier, text, expected):
    r = classifier.classify(text)
    assert r["category"] == expected, f"输入「{text}」期望 {expected}，实际 {r['category']}"


@pytest.mark.parametrize("text,expected", BOUNDARY)
def test_boundary_uncertain(classifier, text, expected):
    r = classifier.classify(text)
    assert r["category"] == expected or r["confidence"] < 0.6, \
        f"无风险输入不应高置信度命中，实际 {r['category']} {r['confidence']}"


def test_confidence_range(classifier):
    for text, _ in CASES:
        r = classifier.classify(text)
        assert 0 <= r["confidence"] <= 1
