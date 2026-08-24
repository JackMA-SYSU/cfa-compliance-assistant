# -*- coding: utf-8 -*-
"""API 端点测试（httpx/TestClient）"""
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "backend"))

from fastapi.testclient import TestClient  # noqa: E402
import main  # noqa: E402


@pytest.fixture(scope="module")
def client():
    with TestClient(main.app) as c:
        yield c


def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"
    assert r.json()["corpus_size"] >= 200


def test_analyze_ok(client):
    r = client.post("/api/analyze", json={"behavior": "客户额外给我一笔奖金"})
    assert r.status_code == 200
    d = r.json()
    assert d["risk_level"] in {"high", "mid", "low"}
    assert d["standards"]


def test_analyze_empty_input_422(client):
    r = client.post("/api/analyze", json={"behavior": ""})
    assert r.status_code == 422


def test_analyze_long_input_truncated(client):
    long_text = "客户送礼" * 2000
    r = client.post("/api/analyze", json={"behavior": long_text})
    assert r.status_code == 200


def test_analyze_missing_field_422(client):
    r = client.post("/api/analyze", json={})
    assert r.status_code == 422
