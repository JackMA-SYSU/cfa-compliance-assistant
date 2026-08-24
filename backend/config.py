# -*- coding: utf-8 -*-
"""全局配置：路径、模型、LLM 供应商"""
import os

# 项目根目录（backend 的上一级）
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))

CORPUS_PATH = os.environ.get("CORPUS_PATH", os.path.join(DATA_DIR, "ethics_corpus.jsonl"))
CHROMA_DIR = os.environ.get("CHROMA_DIR", os.path.join(BACKEND_DIR, "chroma_db"))
CHROMA_COLLECTION = os.environ.get("CHROMA_COLLECTION", "cfae_ethics")
INVERTED_INDEX_PATH = os.path.join(CHROMA_DIR, "inverted_index.json")

# Embedding 模型（本地 sentence-transformers）
EMBEDDING_MODEL = os.environ.get(
    "EMBEDDING_MODEL", "paraphrase-multilingual-MiniLM-L12-v2"
)

# LLM 配置
LLM_API_KEY = os.environ.get("LLM_API_KEY", "")
LLM_BASE_URL = os.environ.get("LLM_BASE_URL", "")  # 兼容 DeepSeek / 通义 / 本地 Ollama
LLM_MODEL = os.environ.get("LLM_MODEL", "deepseek-chat")
LLM_FALLBACK_MODEL = os.environ.get("LLM_FALLBACK_MODEL", "")
LLM_TIMEOUT = float(os.environ.get("LLM_TIMEOUT", "15"))
LLM_TEMPERATURE = float(os.environ.get("LLM_TEMPERATURE", "0.3"))

# 检索参数
RETRIEVAL_TOP_K = int(os.environ.get("RETRIEVAL_TOP_K", "5"))
CLASSIFIER_CONFIDENCE_THRESHOLD = float(os.environ.get("CLASSIFIER_CONFIDENCE_THRESHOLD", "0.6"))

# 缓存
CACHE_CAPACITY = int(os.environ.get("CACHE_CAPACITY", "1000"))
CACHE_SIMILARITY_THRESHOLD = float(os.environ.get("CACHE_SIMILARITY_THRESHOLD", "0.95"))

# API 限流
RATE_LIMIT_PER_MINUTE = int(os.environ.get("RATE_LIMIT_PER_MINUTE", "20"))

# CORS 白名单（逗号分隔）
CORS_ORIGINS = [o.strip() for o in os.environ.get("CORS_ORIGINS", "*").split(",") if o.strip()]
