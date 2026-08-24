# -*- coding: utf-8 -*-
"""LLM 客户端封装

支持多厂商（OpenAI / DeepSeek / 通义千问 / 本地 Ollama），统一接口：
    chat_completion(messages, model, temperature, json_mode) -> dict

容错：主模型失败自动回退备用模型、超时 15s、重试 3 次指数退避、
全部记录到日志；成本监控：记录每次 token 消耗，提供 get_usage_stats()。
"""
import json
import logging
import os
import sys
import threading
import time
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config  # noqa: E402

logger = logging.getLogger("llm_client")

# 各厂商默认 base_url（未配置 LLM_BASE_URL 时按模型前缀推断）
PROVIDER_BASE_URLS = {
    "deepseek": "https://api.deepseek.com",
    "qwen": "https://dashscope.aliyuncs.com/compatible-mode/v1",
    "ollama": "http://localhost:11434/v1",
    "openai": "https://api.openai.com/v1",
}


def _infer_base_url(model: str) -> str:
    for key, url in PROVIDER_BASE_URLS.items():
        if model.lower().startswith(key):
            return url
    return PROVIDER_BASE_URLS["openai"]


class UsageStats:
    """token 消耗监控（线程安全）"""

    def __init__(self):
        self._lock = threading.Lock()
        self.daily = defaultdict(lambda: {"input": 0, "output": 0, "calls": 0})

    def record(self, model, input_tokens, output_tokens):
        day = time.strftime("%Y-%m-%d")
        with self._lock:
            d = self.daily[day]
            d["input"] += input_tokens
            d["output"] += output_tokens
            d["calls"] += 1

    def get_stats(self, days=7):
        out = []
        for day in sorted(self.daily, reverse=True)[:days]:
            d = self.daily[day]
            out.append({"date": day, **dict(d)})
        return out


class LLMClient:
    def __init__(self, api_key=None, base_url=None, model=None,
                 fallback_model=None):
        self.api_key = api_key or config.LLM_API_KEY
        self.base_url = base_url or config.LLM_BASE_URL
        self.model = model or config.LLM_MODEL
        self.fallback_model = fallback_model or config.LLM_FALLBACK_MODEL
        self.timeout = config.LLM_TIMEOUT
        self.usage = UsageStats()
        self._client = None

    def _openai_client(self, base_url):
        from openai import OpenAI
        return OpenAI(api_key=self.api_key or "sk-none", base_url=base_url)

    def _call(self, messages, model, temperature, json_mode, max_retries=3):
        base_url = self.base_url or _infer_base_url(model)
        client = self._openai_client(base_url)
        kwargs = dict(
            model=model,
            messages=messages,
            temperature=temperature,
            timeout=self.timeout,
        )
        if json_mode:
            kwargs["response_format"] = {"type": "json_object"}

        last_err = None
        for attempt in range(max_retries):
            try:
                resp = client.chat.completions.create(**kwargs)
                choice = resp.choices[0].message
                self.usage.record(model,
                                  getattr(resp.usage, "prompt_tokens", 0),
                                  getattr(resp.usage, "completion_tokens", 0))
                return {
                    "content": choice.content or "",
                    "model": model,
                    "input_tokens": getattr(resp.usage, "prompt_tokens", 0),
                    "output_tokens": getattr(resp.usage, "completion_tokens", 0),
                }
            except Exception as e:  # noqa: BLE001
                last_err = e
                logger.warning("LLM 调用失败 (attempt %s/%s, model=%s): %s",
                               attempt + 1, max_retries, model, e)
                time.sleep(min(2 ** attempt, 8))
        raise RuntimeError(f"LLM 调用最终失败: {last_err}")

    def chat_completion(self, messages, model=None, temperature=None,
                        json_mode=True):
        """统一接口。主模型失败自动回退备用模型。"""
        model = model or self.model
        temperature = config.LLM_TEMPERATURE if temperature is None else temperature
        try:
            return self._call(messages, model, temperature, json_mode)
        except Exception as e:  # noqa: BLE001
            if self.fallback_model and self.fallback_model != model:
                logger.warning("主模型失败，回退到 %s", self.fallback_model)
                return self._call(messages, self.fallback_model, temperature, json_mode)
            raise e

    def get_usage_stats(self, days=7):
        return self.usage.get_stats(days)


def parse_json_output(content: str):
    """把 LLM 返回文本解析为 dict，失败返回 None（供规则引擎回退）"""
    if not content:
        return None
    content = content.strip()
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        pass
    # 尝试剥离 markdown 代码块
    import re
    m = re.search(r"\{.*\}", content, re.S)
    if m:
        try:
            return json.loads(m.group(0))
        except json.JSONDecodeError:
            return None
    return None
