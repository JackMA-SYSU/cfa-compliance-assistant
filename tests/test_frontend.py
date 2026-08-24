# -*- coding: utf-8 -*-
"""前端端到端测试（Playwright，可选）

运行前需安装：
    pip install playwright
    playwright install chromium

启动后端后执行：
    pytest tests/test_frontend.py -q
"""
import os

import pytest

pytest.importorskip("playwright.sync_api")

from playwright.sync_api import sync_playwright  # noqa: E402

BASE_URL = os.environ.get("APP_BASE_URL", "http://localhost:8000")


@pytest.fixture(scope="module")
def page():
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.goto(BASE_URL)
        yield page
        browser.close()


def test_title(page):
    assert "合规" in page.title()


def test_analyze_flow(page):
    page.fill("#behavior", "客户送我去打高尔夫并承担差旅费")
    page.click("#analyze-btn")
    # 等待结果卡片出现
    page.wait_for_selector(".risk-card", timeout=15000)
    assert page.inner_text(".risk-card .risk-level").strip() in ["高风险", "中风险", "低风险"]


def test_standards_view(page):
    page.click('.tab[data-view="standards"]')
    page.wait_for_selector(".std-card", timeout=5000)
    assert page.locator(".std-card").count() >= 20


def test_history_view(page):
    page.click('.tab[data-view="history"]')
    page.wait_for_selector(".history-item, .empty", timeout=5000)
