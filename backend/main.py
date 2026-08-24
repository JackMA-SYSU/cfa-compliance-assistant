# -*- coding: utf-8 -*-
"""FastAPI 主服务入口

运行：
    uvicorn main:app --host 0.0.0.0 --port 8000
"""
import logging
import sys
import os
from contextlib import asynccontextmanager

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi import FastAPI  # noqa: E402
from fastapi.middleware.cors import CORSMiddleware  # noqa: E402
from fastapi.staticfiles import StaticFiles  # noqa: E402

import config  # noqa: E402
from models.schemas import HealthResponse  # noqa: E402
from routers.compliance import router as compliance_router  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")
logger = logging.getLogger("main")

VERSION = "1.0.0"


def build_engine():
    """懒加载知识库 + 分类器 + RAG 引擎"""
    from build_kb import EthicsKnowledgeBase
    from services.classifier import RuleBasedClassifier
    from services.rag_engine import RAGEngine

    kb = EthicsKnowledgeBase()
    classifier = RuleBasedClassifier(kb=kb)
    engine = RAGEngine(kb=kb, classifier=classifier)
    return kb, engine


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("正在加载知识库与引擎...")
    app.state.kb, app.state.engine = build_engine()
    app.state.corpus_size = len(app.state.kb.load_corpus())
    logger.info("启动完成，语料 %s 题", app.state.corpus_size)
    yield
    logger.info("关闭服务")


app = FastAPI(title="CFA 道德合规 AI 自检助手", version=VERSION, lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=config.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(compliance_router)


@app.get("/health", response_model=HealthResponse)
async def health():
    corpus_size = getattr(app.state, "corpus_size", 0)
    return HealthResponse(
        status="ok", version=VERSION, corpus_size=corpus_size,
        embedding="sentence-transformers" if os.environ.get("USE_SENTENCE_TRANSFORMERS") == "1" else "tfidf",
    )


# 托管前端 PWA 静态文件（本地一体化部署；也可独立部署到 Vercel）
FRONTEND_DIR = os.path.join(config.BASE_DIR, "frontend")
if os.path.isdir(FRONTEND_DIR):
    app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")
